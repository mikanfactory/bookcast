import asyncio
from typing import List, Optional, Annotated
from logging import getLogger

from google import genai
from pydantic import BaseModel, Field
import operator

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from bookcast.config import GEMINI_API_KEY
from bookcast.view_models import PodcastSetting
from bookcast.path_resolver import (
    build_script_directory,
    resolve_script_path,
)
from bookcast.services.base import BaseService
from bookcast.entities import Chapter

logger = getLogger(__name__)
MAX_RETRY_COUNT = 3


class PodcastTopic(BaseModel):
    title: str = Field(..., description="トピックのタイトル")
    description: str = Field(..., description="トピックの概要")


class TopicSearchResult(BaseModel):
    topics: List[PodcastTopic] = Field(..., description="トピックのリスト")


class EvaluateResult(BaseModel):
    is_valid: bool = Field(..., description="適切か否か")
    feedback_message: str = Field(..., description="フィードバックのリスト")


class State(BaseModel):
    source_text: str = Field(..., description="台本の元となる文章")
    topics: List[PodcastTopic] = Field(
        default_factory=list, description="トピックのリスト"
    )
    script: str = Field(default="", description="台本")
    feedback_messages: Annotated[list[str], operator.add] = Field(
        default_factory=list, description="作成された台本に対するフィードバック"
    )
    retry_count: int = Field(default=0, description="再実行回数")
    is_valid: bool = Field(default=False, description="適切か否か")


class PodCastTopicSearcher(object):
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: State) -> TopicSearchResult:
        prompt_text = """
あなたはトピックを抽出する専門家です。
次の文章を元にして、ポッドキャストの台本を作成しようとしています。
文章を読んで、3から5つのトピックを抽出してください。
source_text:{source_text}
"""

        message = ChatPromptTemplate(
            [
                ("human", prompt_text),
            ]
        )

        chain = message | self.llm.with_structured_output(TopicSearchResult)
        return await chain.ainvoke({"source_text": state.source_text})


def _format_topics(topics: List[PodcastTopic]) -> str:
    acc = "\n"
    for topic in topics:
        acc += f"- タイトル: {topic.title}, 概要: {topic.description}\n"

    return acc


class PodCastScriptWriter(object):
    def __init__(self, llm, podcast_setting: PodcastSetting):
        self.llm = llm
        self.podcast_setting = podcast_setting

    async def run(self, state: State) -> str:
        system_prompt = """
あなたはポッドキャストの台本を作成する専門家です。
今回扱う内容は難しいですが、視聴者は専門知識を持っているため、難しいまま理解できます。
与えられた文章をなるべく端折らず、会話で掘り下げていく形で台本を作成してください。
必ず守るルール:
- ユーザーから与えられたトピックはすべて網羅してください。
- ポッドキャストの長さは気にせず、全部のトピックを詳しく説明してください。
- 本文のみを出力してください。オープニングとエンディングは別で処理します。
- フィードバックがある場合は、それに注意して台本を作成してください。
- 2人の会話形式で台本を書いてください。
- 出力の形式は下記のようにしてください。
**出力例**
Speaker1: こんにちは。今日はいい天気ですね。
Speaker2: 本当ですね。ちょっと暑いくらいですね。
"""
        if state.feedback_messages:
            system_prompt += "フィードバック: {feedback_messages}"

        formated_topics = _format_topics(state.topics)
        prompt_text = f"トピック: {formated_topics}文章: {{source_text}}"

        message = ChatPromptTemplate(
            [
                ("system", system_prompt),
                ("human", prompt_text),
            ]
        )

        chain = message | self.llm | StrOutputParser()
        return await chain.ainvoke({"source_text": state.source_text})


class PodCastScriptEvaluator(object):
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: State) -> EvaluateResult:
        topics = _format_topics(state.topics)
        prompt_text = f"""
あなたはポッドキャストの台本を評価する専門家です。
次の台本を読んで、以下の基準に基づいて評価してください。
- トピックはすべて網羅されているか
- 話のつながりが不自然でないか
- 聞き手にとって十分な情報が提供されているか
適切であればtrueを返してください。
不適切であれば、次に活かせるように必ずフィードバックを返してください。フィードバックは必ず日本語で返してください。
またフィードバックには必ず具体例を入れるようにしてください。
トピック: {topics}
台本: {state.script}
"""

        message = ChatPromptTemplate(
            [
                ("human", prompt_text),
            ]
        )

        chain = message | self.llm.with_structured_output(EvaluateResult)
        return await chain.ainvoke({"script": state.script})


class PodCastOrchestrator(object):
    def __init__(self, llm, podcast_setting: PodcastSetting):
        self.llm = llm
        self.topic_searcher = PodCastTopicSearcher(llm)
        self.script_writer = PodCastScriptWriter(llm, podcast_setting)
        self.script_evaluator = PodCastScriptEvaluator(llm)
        self.graph = self._create_graph()

    async def _search_topics(self, state: State):
        result = await self.topic_searcher.run(state)
        return {
            "topics": result.topics,
        }

    async def _write_script(self, state: State):
        script = await self.script_writer.run(state)
        return {
            "script": script,
        }

    async def _evaluate_script(self, state: State):
        result = await self.script_evaluator.run(state)
        if result.is_valid:
            return {"is_valid": True}
        else:
            return {
                "is_valid": False,
                "retry_count": state.retry_count + 1,
                "feedback_message": [result.feedback_message],
            }

    def _should_retry_or_continue(self, state: State):
        if state.is_valid:
            return True
        elif state.retry_count < MAX_RETRY_COUNT:
            return False
        else:
            return True

    def _create_graph(self):
        graph = StateGraph(State)
        graph.add_node("search_topics", self._search_topics)
        graph.add_node("write_script", self._write_script)
        graph.add_node("evaluate_script", self._evaluate_script)

        graph.set_entry_point("search_topics")
        graph.add_edge("search_topics", "write_script")
        graph.add_edge("write_script", "evaluate_script")
        graph.add_conditional_edges(
            "evaluate_script",
            self._should_retry_or_continue,
            {True: END, False: "write_script"},
        )

        return graph.compile()

    async def run(self, source_text) -> str:
        state = State(source_text=source_text)
        result = await self.graph.ainvoke(state)
        return result["script"]


class ScriptWritingService(BaseService):
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        self.semaphore = asyncio.Semaphore(10)
        self.script_model = "gemini-2.0-flash"

    @staticmethod
    async def _generate_script_for_text(
        podcast_setting: PodcastSetting, chapter: Chapter
    ) -> str:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01
        )
        script_writer_agent = PodCastOrchestrator(llm, podcast_setting)
        response = await script_writer_agent.run(chapter.source_text)
        return response

    async def _generate_chapter_script(
        self, podcast_setting: PodcastSetting, chapter: Chapter
    ) -> str:
        async with self.semaphore:
            script = await self._generate_script_for_text(podcast_setting, chapter)

        script_dir = build_script_directory(chapter.filename)
        script_dir.mkdir(parents=True, exist_ok=True)

        script_path = resolve_script_path(chapter.filename, chapter.chapter_number)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        return script

    def process(self, podcast_setting: PodcastSetting, chapter: Chapter):
        logger.info(f"Generating script for chapter: {str(chapter)}")
        asyncio.run(self._generate_chapter_script(podcast_setting, chapter))
        logger.info(f"Script generated.")
