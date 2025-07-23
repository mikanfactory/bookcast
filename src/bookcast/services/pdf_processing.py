import asyncio
import io
import json
from typing import Optional, Annotated

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
from bookcast.services.base import BaseService, ServiceResult

MAX_RETRY_COUNT = 3


class OCRState(BaseModel):
    page_number: int = Field(..., description="画像のページ番号")
    base64_image: str = Field(default=None, description="対象の画像")
    extracted_string: str = Field(default="", description="画像から読み取れた文字列")
    feedback_messages: Annotated[list[str], operator.add] = Field(
        default=[], description="読み取り結果に対するフィードバック"
    )
    retry_count: int = Field(default=0, description="再実行回数")
    is_valid: bool = Field(default=False, description="適切か否か")


class ImageProcessingResult(BaseModel):
    extracted_string: str = Field(..., description="画像から読み取れた文字列")


class JudgmentResult(BaseModel):
    is_valid: bool = Field(
        ..., description="OCRの結果が適切か否か。適切な場合はtrue。不適切ならfalse"
    )
    feedback_message: str = Field(..., description="読み取り結果に対するフィードバック")


def format_reflections(reflections: list[str]) -> str:
    acc = ""
    for i, reflection in enumerate(reflections):
        acc += f"{i + 1}: {reflection}\n"

    return acc


class OCRExecutorAgent(object):
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: OCRState) -> ImageProcessingResult:
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

        chain = message | self.llm.with_structured_output(ImageProcessingResult)
        return await chain.ainvoke({})


class OCRResultGuardian(object):
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: OCRState) -> JudgmentResult:
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

        chain = message | self.llm.with_structured_output(JudgmentResult)
        return await chain.ainvoke({"extracted_string": state.extracted_string})


class OCROrchestrator(object):
    def __init__(self, llm):
        self.llm = llm
        self.ocr_agent = OCRExecutorAgent(llm)
        self.guardian = OCRResultGuardian(llm)
        self.graph = self._create_graph()

    async def _execute_ocr(self, state: OCRState):
        result = await self.ocr_agent.run(state)
        return {
            "extracted_string": result.extracted_string,
        }

    async def _judge_result(self, state: OCRState):
        result = await self.guardian.run(state)
        if result.is_valid:
            return {"is_valid": True}
        else:
            return {
                "is_valid": False,
                "retry_count": state.retry_count + 1,
                "feedback_messages": [result.feedback_message],
            }

    def _should_retry_or_continue(self, state: OCRState):
        if state.is_valid:
            return True
        elif state.retry_count < MAX_RETRY_COUNT:
            return False
        else:
            return True

    def _create_graph(self):
        graph = StateGraph(OCRState)
        graph.add_node("ocr_execution", self._execute_ocr)
        graph.add_node("result_judgment", self._judge_result)

        graph.set_entry_point("ocr_execution")
        graph.add_edge("ocr_execution", "result_judgment")
        graph.add_conditional_edges(
            "result_judgment",
            self._should_retry_or_continue,
            {True: END, False: "ocr_execution"},
        )

        return graph.compile()

    async def run(self, page_number: int, base64_image: str) -> ImageProcessingResult:
        state = OCRState(page_number=page_number, base64_image=base64_image)
        return await self.graph.ainvoke(state)


class PDFProcessingService(BaseService):
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.semaphore = asyncio.Semaphore(10)

    def convert_pdf_to_images(self, filename: str) -> ServiceResult:
        self._log_info(f"Converting PDF to images: {filename}")

        pdf_path = build_downloads_path(filename)
        if not pdf_path.exists():
            return ServiceResult.failure(f"PDF file not found: {filename}")

        images = convert_from_path(pdf_path)

        image_dir = build_image_directory(filename)
        image_dir.mkdir(parents=True, exist_ok=True)

        for i, image in enumerate(images):
            page_number = i + 1
            image_path = resolve_image_path(filename, page_number)
            image.save(image_path, "PNG")

        self._log_info(f"Successfully converted {len(images)} pages to images")
        return ServiceResult.success(images)

    async def _extract_text_from_image(
        self, page_number: int, image: Image.Image
    ) -> str:
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

    async def _extract_and_save_text(
        self, filename: str, page_number: int, image: Image.Image
    ) -> str:
        async with self.semaphore:
            extracted_text = await self._extract_text_from_image(page_number, image)

        text_dir = build_text_directory(filename)
        text_dir.mkdir(parents=True, exist_ok=True)

        text_path = resolve_text_path(filename, page_number)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        return extracted_text

    async def extract_text_from_pdf(self, filename: str) -> ServiceResult:
        self._log_info(f"Extracting text from PDF: {filename}")

        pdf_path = build_downloads_path(filename)
        if not pdf_path.exists():
            return ServiceResult.failure(f"PDF file not found: {filename}")

        images = convert_from_path(pdf_path)

        tasks = [
            self._extract_and_save_text(filename, i + 1, image)
            for i, image in enumerate(images)
        ]

        texts = await asyncio.gather(*tasks)

        self._log_info(f"Successfully extracted text from {len(texts)} pages")
        return ServiceResult.success(texts)

    def process_pdf(self, filename: str) -> ServiceResult:
        self._log_info(f"Starting complete PDF processing: {filename}")

        # Convert PDF to images
        images_result = self.convert_pdf_to_images(filename)
        if not images_result.success:
            return images_result

        # Extract text from images
        text_result = asyncio.run(self.extract_text_from_pdf(filename))
        if not text_result.success:
            return text_result

        summary = {
            "filename": filename,
            "pages_processed": len(images_result.data),
            "texts_extracted": len(text_result.data),
        }

        self._log_info(f"PDF processing completed successfully: {summary}")
        return ServiceResult.success(summary)
