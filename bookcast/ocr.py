import io
import logging
from typing import Optional
from PIL import Image
from google import genai
from google.genai import types
from bookcast.config import GEMINI_API_KEY


logger = logging.getLogger(__name__)


class GeminiOCR:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def extract_text_from_image(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_data = buffer.getvalue()

        prompt = (
            "この画像から日本語と英語のテキストを抽出してください。章のタイトルや見出しを特に注意深く読み取ってください。テキストのみを返してください。",
        )

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_data,
                    mime_type="image/png",
                ),
                prompt,
            ],
        )

        extracted_text = response.text.strip()

        return extracted_text


def extract_text_from_image(image: Image.Image) -> str:
    ocr = GeminiOCR(GEMINI_API_KEY)
    return ocr.extract_text_from_image(image)
