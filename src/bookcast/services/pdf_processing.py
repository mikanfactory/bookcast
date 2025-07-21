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


class OCRState(BaseModel):
    page_number: int = Field(..., description="画像のページ番号")
    base64_image: str = Field(default=None, description="対象の画像")
    extracted_string: Optional[str] = Field(default="", description="画像から読み取れた文字列")
    error_message: Optional[str] = Field(default="")
    error_code: Optional[str] = Field(default="")
    is_valid: Optional[bool] = Field(
        default=False,
        description="True if the OCR result is valid, False if it contains errors.",
    )


class ImageProcessingResult(BaseModel):
    extracted_string: str = Field(default="", description="画像から読み取れた文字列")
    error_message: Optional[str] = Field(default="", description="エラーメッセージ")
    error_code: Optional[str] = Field(default="", description="")


class JudgmentResult(BaseModel):
    is_valid: bool = Field()
    error_message: Optional[str] = Field(default="")


class OCRExecutorAgent(object):
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: OCRState) -> dict:
        prompt_text = (
            "この画像に含まれる文字を抽出してください。"
            "章や節のタイトルは含めてください。一方でページ番号などは含めないようにしてください。"
            "また抽出できた文字のみを出力してください。"
            "次のような状況があります:\n"
            "1. 画像に文字が含まれない場合"
            "2. 文字が歪んでいる、文字が薄い等で文字が読み取れない場合"
            "画像のうち1/4以上が読み取れない、もしくは文字が含まれない場合は、上のエラーコードとエラーメッセージを返してください。"
            "部分的に読み取れなくても、読み取れる部分がある場合は、読み取れる部分の文字列を返してください。"
        )

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
        result: ImageProcessingResult = await chain.ainvoke({})
        return {
            "extracted_string": result.extracted_string,
            "error_code": result.error_code,
            "error_message": result.error_message,
        }


class OCRResultGuardian(object):
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: OCRState) -> dict:
        prompt_text = (
            "あなたはOCR結果の検証を行うAIです。"
            "この画像はOCR処理をしたが文字が読み取れなかった画像です。"
            "エラーメッセージを確認し、その通りであればtrueを返してください。"
            "もし正常な文字列が含まれている場合はfalseを返し、理由も教えて下さい。"
            "エラーメッセージ:{error_message}"
        )

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
        result: JudgmentResult = await chain.ainvoke(
            {"error_message": state.error_message}
        )
        return {"is_valid": result.is_valid, "error_message": result.error_message}


class OCROrchestrator(object):
    def __init__(self, llm):
        self.llm = llm
        self.ocr_agent = OCRExecutorAgent(llm)
        self.guardian = OCRResultGuardian(llm)
        self.graph = self._create_graph()

    async def _execute_ocr(self, state: OCRState):
        result = await self.ocr_agent.run(state)
        if result["error_code"] != "":
            print(json.dumps(result))
        return result

    async def _judge_result(self, state: OCRState):
        result = await self.guardian.run(state)
        if result["error_message"] != "":
            print(json.dumps(result))
        return result

    def _create_graph(self):
        graph = StateGraph(OCRState)
        graph.add_node("ocr_execution", self._execute_ocr)
        graph.add_node("result_judgment", self._judge_result)

        graph.set_entry_point("ocr_execution")
        graph.add_edge("ocr_execution", "result_judgment")
        graph.add_conditional_edges(
            "result_judgment",
            lambda state: state.is_valid,
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
            page_num = i + 1
            image_path = resolve_image_path(filename, page_number)
            image.save(image_path, "PNG")

        self._log_info(f"Successfully converted {len(images)} pages to images")
        return ServiceResult.success(images)


    async def _extract_text_from_image(self, page_number: int, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_data = buffer.getvalue()
        base64_image = base64.b64encode(image_data).decode("utf-8")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01
        )

        ocr_agent = OCROrchestrator(llm)

        response = await ocr_agent.run(page_number, base64_image)
        return response['extracted_string']

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
