from bookcast.file_paths import build_text_directory
from bookcast.file_paths import build_downloads_path
import io
import asyncio
import logging
from pdf2image import convert_from_path
from PIL import Image
from google import genai
from google.genai import types
from bookcast.config import GEMINI_API_KEY


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
            "この画像から日本語と英語のテキストを抽出してください。章のタイトルや見出しを特に注意深く読み取ってください。テキストのみを返してください。",
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

        text_path = text_dir / f"page_{page_num:03d}.txt"
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
