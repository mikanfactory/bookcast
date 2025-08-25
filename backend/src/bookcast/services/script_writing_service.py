import asyncio
import operator
from logging import getLogger
from typing import Annotated, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langsmith import traceable
from pydantic import BaseModel, Field

from bookcast.config import GEMINI_API_KEY
from bookcast.entities import Chapter, ChapterStatus, Project
from bookcast.services.chapter_service import ChapterService

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
    topics: List[PodcastTopic] = Field(default_factory=list, description="トピックのリスト")
    script: str = Field(default="", description="台本")
    feedback_messages: Annotated[list[str], operator.add] = Field(
        default_factory=list, description="作成された台本に対するフィードバック"
    )
    retry_count: int = Field(default=0, description="再実行回数")
    is_valid: bool = Field(default=False, description="適切か否か")


class PodcastTopicSearcher:
    def __init__(self, llm):
        self.llm = llm

    @traceable(name="PodcastTopicSearcher")
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


class PodcastScriptWriter:
    def __init__(self, llm):
        self.llm = llm

    @traceable(name="PodcastScriptWriter")
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


class PodcastScriptEvaluator:
    def __init__(self, llm):
        self.llm = llm

    @traceable(name="PodcastScriptEvaluator")
    async def run(self, state: State) -> EvaluateResult:
        if state.script is None:
            return EvaluateResult(is_valid=False, feedback_message="台本がありません。作成してください。")

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


class PodcastOrchestrator:
    def __init__(self, llm):
        self.llm = llm
        self.topic_searcher = PodcastTopicSearcher(llm)
        self.script_writer = PodcastScriptWriter(llm)
        self.script_evaluator = PodcastScriptEvaluator(llm)
        self.graph = self._create_graph()

    async def _search_topics(self, state: State) -> dict:
        result = await self.topic_searcher.run(state)
        return {
            "topics": result.topics,
        }

    async def _write_script(self, state: State) -> dict:
        script = await self.script_writer.run(state)
        return {
            "script": script,
        }

    async def _evaluate_script(self, state: State) -> dict:
        result = await self.script_evaluator.run(state)
        if result.is_valid:
            return {"is_valid": True}
        else:
            return {
                "is_valid": False,
                "retry_count": state.retry_count + 1,
                "feedback_message": [result.feedback_message],
            }

    @staticmethod
    def _should_retry_or_continue(state: State) -> bool:
        if state.is_valid:
            return True
        elif state.retry_count < MAX_RETRY_COUNT:
            return False
        else:
            return True

    def _create_graph(self) -> CompiledStateGraph:
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


class ScriptWritingService:
    def __init__(self, chapter_service: ChapterService):
        self.semaphore = asyncio.Semaphore(10)
        self.chapter_service = chapter_service

    @staticmethod
    async def _generate(chapter: Chapter) -> str:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01)
        script_writer_agent = PodcastOrchestrator(llm)
        response = await script_writer_agent.run(chapter.extracted_text)
        return response

    async def _generate_script(self, chapter: Chapter):
        async with self.semaphore:
            logger.info(f"Generating script for chapter: {str(chapter)}")
            script = await self._generate(chapter)

        chapter.status = ChapterStatus.writing_script_completed
        chapter.script = script
        self.chapter_service.update(chapter)
        logger.info(f"Completed script generation for chapter: {str(chapter)}")

    async def _generate_scripts(self, chapters: list[Chapter]):
        tasks = []
        for chapter in chapters:
            if chapter.status == ChapterStatus.start_writing_script:
                tasks.append(self._generate_script(chapter))
            else:
                logger.info(f"Skipping script generation for chapter (already completed): {str(chapter)}")

        return await asyncio.gather(*tasks)

    async def process(self, project: Project, chapters: list[Chapter]):
        logger.info("Start writing script.")
        await self._generate_scripts(chapters)
        logger.info("End writing script.")
