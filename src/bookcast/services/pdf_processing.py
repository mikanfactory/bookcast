"""
PDF processing service that handles PDF to image conversion and OCR.
"""

import asyncio
import io
from typing import Optional

from google import genai
from google.genai import types
from pdf2image import convert_from_path
from PIL import Image

from bookcast.config import GEMINI_API_KEY
from bookcast.path_resolver import (
    build_downloads_path,
    build_image_directory,
    build_text_directory,
    resolve_image_path,
    resolve_text_path,
)
from bookcast.services.base import BaseService, ServiceResult


class PDFProcessingService(BaseService):
    """Service for handling PDF processing operations."""

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
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
        Extract text from a single image using Gemini OCR.

        Args:
            image: PIL Image object

        Returns:
            Extracted text as string
        """
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_data = buffer.getvalue()

        prompt = (
            "この画像に含まれる文字を抽出してください。"
            "構造に沿って文章を抽出してください。タイトルやページ番号などは含めないようにしてください。"
            "また抽出した文字のみを出力してください。"
            "読み取れなければ読み取れない理由を答えてください。"
            "わからないことがあれば質問してください。"
        )

        response = self.gemini_client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_data,
                    mime_type="image/png",
                ),
                prompt,
            ],
            config=types.GenerateContentConfig(temperature=0.01),
        )

        resp = await response
        return resp.text.strip()

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
