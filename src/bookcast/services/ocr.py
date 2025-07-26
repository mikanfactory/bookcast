import asyncio
import io
from typing import Annotated
from logging import getLogger

import base64
from pdf2image import convert_from_path
from PIL import Image

import operator
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from bookcast.config import GEMINI_API_KEY
from bookcast.path_resolver import (
    build_downloads_path,
    build_image_directory,
    build_text_directory,
    resolve_image_path,
    resolve_text_path,
)

logger = getLogger(__name__)
MAX_RETRY_COUNT = 3


class State(BaseModel):
    page_number: int = Field(..., description="画像のページ番号")
    base64_image: str = Field(default=None, description="対象の画像")
    extracted_string: str = Field(default="", description="画像から読み取れた文字列")
    feedback_messages: Annotated[list[str], operator.add] = Field(
        default=[], description="読み取り結果に対するフィードバック"
    )
    retry_count: int = Field(default=0, description="再実行回数")
    is_valid: bool = Field(default=False, description="適切か否か")


class OCRResult(BaseModel):
    extracted_string: str = Field(..., description="画像から読み取れた文字列")


class EvaluateResult(BaseModel):
    is_valid: bool = Field(
        ..., description="OCRの結果が適切か否か。適切な場合はtrue。不適切ならfalse"
    )
    feedback_message: str = Field(..., description="読み取り結果に対するフィードバック")


def format_reflections(reflections: list[str]) -> str:
    acc = ""
    for i, reflection in enumerate(reflections):
        acc += f"{i + 1}: {reflection}\n"

    return acc


class OCRExecutor:
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: State) -> OCRResult:
        prompt_text = """
あなたはOCRを行うAIです。この画像に含まれる文字を抽出してください。
抽出したいもの:
- 本文
- 章や節のタイトル
抽出しなくていいもの:
- 脚注などの注
- 図や、図中の文章
- キャプション
- ページ番号
"""

        if state.retry_count > 0:
            reflection_text = format_reflections(state.feedback_messages)
            prompt_text += f"\n\n実行する際に、以下の過去の他社からのフィードバックを考慮すること。\n{reflection_text}"

        message = ChatPromptTemplate(
            [
                (
                    "human",
                    [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image",
                            "source_type": "base64",
                            "data": state.base64_image,
                            "mime_type": "image/png",
                        },
                    ],
                )
            ]
        )

        chain = message | self.llm.with_structured_output(OCRResult)
        return await chain.ainvoke({})


class OCRResultEvaluator:
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: State) -> EvaluateResult:
        prompt_text = """
あなたはOCRの結果の検証を行うAIです。
このOCRの結果は次のものを対象としています。
抽出したいもの:
- 本文
- 章や節のタイトル
抽出しなくていいもの:
- 脚注などの注
- 図や、図中の文章
- キャプション
- ページ番号
あなたはまず画像から文章を読み取り、その後に受け取った文章と照らし合わせてください。
適切であればtrueを返してください。
不適切であれば、次に活かせるように必ずフィードバックを返してください。フィードバックは必ず日本語で返してください。
またフィードバックにはどこが読み取れていないか、具体例を入れるようにしてください。
OCR結果: {extracted_string}
"""

        message = ChatPromptTemplate(
            [
                (
                    "human",
                    [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image",
                            "source_type": "base64",
                            "data": state.base64_image,
                            "mime_type": "image/png",
                        },
                    ],
                )
            ]
        )

        chain = message | self.llm.with_structured_output(EvaluateResult)
        return await chain.ainvoke({"extracted_string": state.extracted_string})


class OCROrchestrator:
    def __init__(self, llm):
        self.llm = llm
        self.ocr_agent = OCRExecutor(llm)
        self.guardian = OCRResultEvaluator(llm)
        self.graph = self._create_graph()

    async def _execute_ocr(self, state: State):
        result = await self.ocr_agent.run(state)
        return {
            "extracted_string": result.extracted_string,
        }

    async def _evaluate_ocr_result(self, state: State):
        result = await self.guardian.run(state)
        if result.is_valid:
            return {"is_valid": True}
        else:
            return {
                "is_valid": False,
                "retry_count": state.retry_count + 1,
                "feedback_messages": [result.feedback_message],
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
        graph.add_node("execute_ocr", self._execute_ocr)
        graph.add_node("evaluate_ocr_result", self._evaluate_ocr_result)

        graph.set_entry_point("execute_ocr")
        graph.add_edge("execute_ocr", "evaluate_ocr_result")
        graph.add_conditional_edges(
            "evaluate_ocr_result",
            self._should_retry_or_continue,
            {True: END, False: "execute_ocr"},
        )

        return graph.compile()

    async def run(self, page_number: int, base64_image: str) -> OCRResult:
        state = State(page_number=page_number, base64_image=base64_image)
        return await self.graph.ainvoke(state)


class OCRService:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(10)

    def _save_text(self, filename: str, page_number: int, extracted_text: str):
        text_dir = build_text_directory(filename)
        text_dir.mkdir(parents=True, exist_ok=True)

        text_path = resolve_text_path(filename, page_number)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)

    def _save_image(self, filename: str, page_number: int, image: Image.Image):
        image_dir = build_image_directory(filename)
        image_dir.mkdir(parents=True, exist_ok=True)

        image_path = resolve_image_path(filename, page_number)
        image.save(image_path, "PNG")

    @staticmethod
    async def _extract_text_from_image(page_number: int, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_data = buffer.getvalue()
        base64_image = base64.b64encode(image_data).decode("utf-8")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01
        )

        ocr_agent = OCROrchestrator(llm)

        response = await ocr_agent.run(page_number, base64_image)
        return response["extracted_string"]

    async def _extract_text(self, filename: str, page_number: int, image: Image.Image) -> str:
        async with self.semaphore:
            extracted_text = await self._extract_text_from_image(page_number, image)

        self._save_text(filename, page_number, extracted_text)
        self._save_image(filename, page_number, image)

        return extracted_text

    async def _extract_text_from_pdf(self, filename: str):
        logger.info(f"Extracting text from PDF: {filename}")

        pdf_path = build_downloads_path(filename)
        images = convert_from_path(pdf_path)

        tasks = [
            self._extract_text(filename, i + 1, image)
            for i, image in enumerate(images)
        ]

        await asyncio.gather(*tasks)

    def process_pdf(self, filename: str):
        logger.info(f"Starting complete PDF processing: {filename}")
        asyncio.run(self._extract_text_from_pdf(filename))
        logger.info(f"Completed complete PDF processing: {filename}")
