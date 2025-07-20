"""
PDF processing service that handles PDF to image conversion and OCR.
"""

import asyncio
import io
from typing import Optional

import base64
from pdf2image import convert_from_path
from PIL import Image

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
    base64_image: str = Field()
    extracted_string: Optional[str]= Field(default=None)
    error_message: Optional[str] = Field(default=None)
    error_code: Optional[str] = Field(default=None)
    is_valid: Optional[bool] = Field(default=None, description="True if the OCR result is valid, False if it contains errors.")


class ImageProcessingResult(BaseModel):
    extracted_string: str = Field()
    error_message: Optional[str] = Field(default=None)
    error_code: Optional[str] = Field(default=None)


class JudgmentResult(BaseModel):
    is_valid: bool = Field(description="True if the OCR result is valid, False if it contains errors.")
    error_message: Optional[str] = Field(default=None, description="Error message if the result is invalid.")


class OCRExecutorAgent(object):
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: OCRState) -> ImageProcessingResult:
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
            ("human", [
                {"type": "text", "text": prompt_text},
                {
                    "type": "image",
                    "source_type": f"base64",
                    "data": state.base64_image,
                    "mime_type": "image/png"
                }
            ])
        )

        chain = message | self.llm.with_structured_output(ImageProcessingResult)
        return await chain.ainvoke({})


class OCRResultGuardian(object):
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: OCRState)-> bool:
        if state.error_code is None:
            return True

        prompt_text = (
            "あなたはOCR結果の検証を行うAIです。"
            "この画像はOCR処理をしたが文字が読み取れなかった画像です。"
            "エラーメッセージを確認し、その通りであればtrueを返してください。"
            "もし正常な文字列が含まれている場合はfalseを返し、理由も教えて下さい。"
            "エラーメッセージ:{error_message}"
        )

        message = ChatPromptTemplate(
            ("human", [
                {"type": "text", "text": prompt_text},
                {
                    "type": "image",
                    "source_type": f"base64",
                    "data": state.base64_image,
                    "mime_type": "image/png"
                },
                {"type": "structured", "data": state.ocr_result}
            ])
        )

        chain = message | self.llm.with_structured_output(JudgmentResult)
        return await chain.ainvoke({"error_message": state.error_message})


class OCROrchestrator(object):
    def __init__(self, llm):
        self.llm = llm
        ocr_agent = OCRExecutorAgent(llm)
        guardian = OCRResultGuardian(llm)

        state = StateGraph(OCRState)
        state.add_node("ocr_execution", ocr_agent)
        state.add_node("result_judgment", guardian)

        state.set_entry_point("ocr_execution")
        state.add_edge("ocr_execution", "result_judgment")
        state.add_conditional_edges(
            "result_judgment",
            lambda state: state.is_valid,
            {True: END, False: "ocr_execution"}
        )

        self.compiled = state.compile()

    async def run(self, base64_image: str) -> ImageProcessingResult:
        state = OCRState(base64_image=base64_image)
        return await self.compiled.ainvoke(state)


class PDFProcessingService(BaseService):
    """Service for handling PDF processing operations."""

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.semaphore = asyncio.Semaphore(10)

    def convert_pdf_to_images(self, filename: str) -> ServiceResult:
        """
        Convert PDF to images and save them to disk.

        Args:
            filename: The name of the PDF file

        Returns:
            ServiceResult with list of Image objects
        """
        try:
            self._log_info(f"Converting PDF to images: {filename}")

            pdf_path = build_downloads_path(filename)
            if not pdf_path.exists():
                return ServiceResult.failure(f"PDF file not found: {filename}")

            images = convert_from_path(pdf_path)

            # Save images to disk
            image_dir = build_image_directory(filename)
            image_dir.mkdir(parents=True, exist_ok=True)

            for i, image in enumerate(images):
                page_num = i + 1
                image_path = resolve_image_path(filename, page_num)
                image.save(image_path, "PNG")

            self._log_info(f"Successfully converted {len(images)} pages to images")
            return ServiceResult.success(images)

        except Exception as e:
            error_msg = f"Failed to convert PDF to images: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    async def _extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from a single image using Gemini OCR via LangChain.

        Args:
            image: PIL Image object

        Returns:
            Extracted text as string
        """

        # Convert PIL Image to base64
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_data = buffer.getvalue()
        base64_image = base64.b64encode(image_data).decode('utf-8')


        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.01
        )

        ocr_agent = OCRExecutorAgent(llm)

        # Process the message
        response = await ocr_agent.run(base64_image)
        return response.content.strip()

    async def _extract_and_save_text(
        self, filename: str, page_num: int, image: Image.Image
    ) -> str:
        """
        Extract text from image and save to file.

        Args:
            filename: The name of the PDF file
            page_num: Page number
            image: PIL Image object

        Returns:
            Extracted text
        """
        async with self.semaphore:
            extracted_text = await self._extract_text_from_image(image)

        # Save text to file
        text_dir = build_text_directory(filename)
        text_dir.mkdir(parents=True, exist_ok=True)

        text_path = resolve_text_path(filename, page_num)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        return extracted_text

    async def extract_text_from_pdf(self, filename: str) -> ServiceResult:
        """
        Extract text from all pages of a PDF using OCR.

        Args:
            filename: The name of the PDF file

        Returns:
            ServiceResult with list of extracted texts
        """
        try:
            self._log_info(f"Extracting text from PDF: {filename}")

            pdf_path = build_downloads_path(filename)
            if not pdf_path.exists():
                return ServiceResult.failure(f"PDF file not found: {filename}")

            images = convert_from_path(pdf_path)

            # Extract text from all images concurrently
            tasks = [
                self._extract_and_save_text(filename, i + 1, image)
                for i, image in enumerate(images)
            ]

            texts = await asyncio.gather(*tasks)

            self._log_info(f"Successfully extracted text from {len(texts)} pages")
            return ServiceResult.success(texts)

        except Exception as e:
            error_msg = f"Failed to extract text from PDF: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def process_pdf(self, filename: str) -> ServiceResult:
        """
        Complete PDF processing: convert to images and extract text.

        Args:
            filename: The name of the PDF file

        Returns:
            ServiceResult with processing summary
        """
        try:
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

        except Exception as e:
            error_msg = f"Failed to process PDF: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)
