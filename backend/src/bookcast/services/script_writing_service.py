import asyncio
from logging import getLogger
from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.func import entrypoint, task
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
    feedback_message: str = Field(..., description="フィードバックメッセージ")


@task
async def search_topics(llm, source_text: str) -> List[PodcastTopic]:
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

    chain = message | llm.with_structured_output(TopicSearchResult)
    result = await chain.ainvoke({"source_text": source_text})
    return result.topics


def _format_topics(topics: List[PodcastTopic]) -> str:
    acc = "\n"
    for topic in topics:
        acc += f"- タイトル: {topic.title}, 概要: {topic.description}\n"

    return acc


@task
async def write_script(llm, source_text: str, topics: List[PodcastTopic], feedback_messages: List[str] = None) -> str:
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
- 1人は教授（Speaker1）、もう1人は学生（Speaker2）です。
- 教授はトピックに関する深い知識を持っており、聞き手は基礎知識を持っていますが、詳しくは知りません。
- 教授が流れを作りつつ、学生のするどい質問を交えながら、トピックを深掘りしていく形にしてください。
- 出力の形式は下記のようにしてください。
**出力例**
Speaker1: こんにちは。今日はいい天気ですね。
Speaker2: 本当ですね。ちょっと暑いくらいですね。
"""
    if feedback_messages:
        system_prompt += f"フィードバック: {', '.join(feedback_messages)}"

    formated_topics = _format_topics(topics)
    prompt_text = f"トピック: {formated_topics}\n文章: {{source_text}}"

    message = ChatPromptTemplate(
        [
            ("system", system_prompt),
            ("human", prompt_text),
        ]
    )

    chain = message | llm | StrOutputParser()
    return await chain.ainvoke({"source_text": source_text})


@task
async def evaluate_script(llm, script: str, topics: List[PodcastTopic]) -> EvaluateResult:
    if not script:
        return EvaluateResult(is_valid=False, feedback_message="台本がありません。作成してください。")

    topics_formatted = _format_topics(topics)
    prompt_text = f"""
あなたはポッドキャストの台本を評価する専門家です。
次の台本を読んで、以下の基準に基づいて評価してください。
- トピックはすべて網羅されているか
- 話のつながりが不自然でないか
- 聞き手にとって十分な情報が提供されているか
適切であればtrueを返してください。
不適切であれば、次に活かせるように必ずフィードバックを返してください。フィードバックは必ず日本語で返してください。
またフィードバックには必ず具体例を入れるようにしてください。
トピック: {topics_formatted}
台本: {script}
"""

    message = ChatPromptTemplate(
        [
            ("human", prompt_text),
        ]
    )

    chain = message | llm.with_structured_output(EvaluateResult)
    return await chain.ainvoke({"script": script})


@entrypoint()
async def script_writing_workflow(source_text: str, llm) -> str:
    topics = await search_topics(llm, source_text)

    feedback_messages = []
    retry_count = 0
    script = ""

    while retry_count < MAX_RETRY_COUNT:
        script = await write_script(llm, source_text, topics, feedback_messages)
        evaluation = await evaluate_script(llm, script, topics)

        if evaluation.is_valid:
            return script

        feedback_messages.append(evaluation.feedback_message)
        retry_count += 1

    return script


class ScriptWritingService:
    def __init__(self, chapter_service: ChapterService):
        self.semaphore = asyncio.Semaphore(10)
        self.chapter_service = chapter_service

    @staticmethod
    async def _generate(chapter: Chapter) -> str:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01)
        response = await script_writing_workflow.ainvoke(
            {"source_text": chapter.extracted_text, "llm": llm}, config={"run_name": "ScriptWritingAgent"}
        )
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
