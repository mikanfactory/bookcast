import io
import asyncio
import logging

from pdf2image import convert_from_path
from PIL import Image
from google import genai
from google.genai import types
from bookcast.config import GEMINI_API_KEY
from bookcast.path_resolver import (
    build_text_directory,
    build_downloads_path,
    resolve_text_path,
)

logger = logging.getLogger(__name__)


class GeminiOCR:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.semaphore = asyncio.Semaphore(10)

    async def extract(self, image: Image.Image) -> str:
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

        response = self.client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_data,
                    mime_type="image/png",
                ),
                prompt,
            ],
            config=types.GenerateContentConfig(
                temperature=0.01
            )
        )
        resp = await response
        extracted_text = resp.text.strip()

        return extracted_text

    async def extract_text(
        self, filename: str, page_num: int, image: Image.Image
    ) -> str:
        async with self.semaphore:
            extracted_text = await self.extract(image)

        text_dir = build_text_directory(filename)
        text_dir.mkdir(parents=True, exist_ok=True)

        text_path = resolve_text_path(filename, page_num)
        with open(text_path, "w") as f:
            f.write(extracted_text)

        return extracted_text


async def combine(filename: str):
    ocr = GeminiOCR(GEMINI_API_KEY)

    pdf_path = build_downloads_path(filename)

    images = convert_from_path(pdf_path)
    tasks = [ocr.extract_text(filename, n + 1, image) for n, image in enumerate(images)]

    await asyncio.gather(*tasks)


def extract_text(filename: str):
    asyncio.run(combine(filename))


async def __combine():
    filename = "プログラマー脳.pdf"
    start_page, end_page = 58, 72

    ocr = GeminiOCR(GEMINI_API_KEY)
    pdf_path = build_downloads_path(filename)

    images = convert_from_path(pdf_path)

    tasks = []
    for n, image in enumerate(images):
        if start_page <= n + 1 <= end_page:
            extracted_text = await ocr.extract_text(filename, n + 1, image)
            print(f"Page {n + 1} extracted text: {extracted_text}")

    await asyncio.gather(*tasks)


def main():
    asyncio.run(__combine())
