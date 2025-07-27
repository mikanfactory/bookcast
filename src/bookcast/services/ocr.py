import asyncio
import base64
import io
from logging import getLogger
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from pdf2image import convert_from_path
from PIL import Image
from pydantic import BaseModel, Field

from bookcast.config import GEMINI_API_KEY
from bookcast.path_resolver import (
    build_downloads_path,
    build_image_directory,
    build_text_directory,
    resolve_image_path,
    resolve_text_path,
)

logger = getLogger(__name__)


class State(BaseModel):
    page_number: int = Field(..., description="画像のページ番号")
    base64_image: str = Field(default=None, description="対象の画像")
    extracted_string: str = Field(default="", description="画像から読み取れた文字列")
    is_valid: bool = Field(default=False, description="適切か否か")
    calibrated_string: str = Field(default="", description="校正後の文字列")


class OCRResult(BaseModel):
    extracted_string: str = Field(..., description="画像から読み取れた文字列")
    error_reason: str = Field(default="", description="画像から文字を読み取れなかった理由")


class EvaluateResult(BaseModel):
    is_valid: bool = Field(..., description="OCRの結果が適切か否か。適切な場合はtrue。不適切ならfalse")
    calibrated_string: str = Field(..., description="校正後の文字列")
    calibration_reason: str = Field(default="", description="校正理由")


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
画像から読み取れない場合は理由を記述してください。
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

        chain = message | self.llm.with_structured_output(OCRResult)
        return await chain.ainvoke({})


class OCRResultEditor:
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: State) -> EvaluateResult:
        prompt_text = """
あなたはOCRの結果の校正を行うAIです。
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
不適切であれば、校正を行い、その文字列を返してください。その際に校正理由も記述してください。
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
        self.evaluator = OCRResultEditor(llm)
        self.graph = self._create_graph()

    async def _execute_ocr(self, state: State) -> dict:
        result = await self.ocr_agent.run(state)
        return {
            "extracted_string": result.extracted_string,
        }

    async def _calibrate_result(self, state: State) -> dict:
        result = await self.evaluator.run(state)
        if result.is_valid:
            return {"is_valid": True}
        else:
            return {
                "is_valid": False,
                "calibrated_string": result.calibrated_string,
            }

    def _create_graph(self) -> CompiledStateGraph:
        graph = StateGraph(State)
        graph.add_node("execute_ocr", self._execute_ocr)
        graph.add_node("calibrate_result", self._calibrate_result)

        graph.set_entry_point("execute_ocr")
        graph.add_edge("execute_ocr", "calibrate_result")

        return graph.compile()

    async def run(self, page_number: int, base64_image: str) -> str:
        state = State(page_number=page_number, base64_image=base64_image)
        result = await self.graph.ainvoke(state, config={"run_name": "OCRAgent"})

        if result["is_valid"]:
            return result["extracted_string"]
        else:
            return result["calibrated_string"]


class OCRService:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(10)

    @staticmethod
    def _save_text(filename: str, page_number: int, extracted_text: str) -> None:
        text_dir = build_text_directory(filename)
        text_dir.mkdir(parents=True, exist_ok=True)

        text_path = resolve_text_path(filename, page_number)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)

    @staticmethod
    def _save_image(filename: str, page_number: int, image: Image.Image) -> None:
        image_dir = build_image_directory(filename)
        image_dir.mkdir(parents=True, exist_ok=True)

        image_path = resolve_image_path(filename, page_number)
        image.save(image_path, "PNG")

    @staticmethod
    def _image_to_base64_png(image: Image.Image) -> str:
        with io.BytesIO() as buf:
            image.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()

    async def _extract(self, page_number: int, image: Image.Image) -> str:
        base64_image = self._image_to_base64_png(image)

        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01)

        ocr_agent = OCROrchestrator(llm)

        response = await ocr_agent.run(page_number, base64_image)
        return response

    async def _extract_text(self, filename: str, page_number: int, image: Image.Image) -> str:
        async with self.semaphore:
            extracted_text = await self._extract(page_number, image)

        self._save_text(filename, page_number, extracted_text)
        self._save_image(filename, page_number, image)

        return extracted_text

    async def _extract_text_from_pdf(self, filename: str, page_number: Optional[int] = None) -> int:
        pdf_path = build_downloads_path(filename)
        images = convert_from_path(pdf_path)

        if page_number is not None:
            tasks = [self._extract_text(filename, page_number, images[page_number - 1])]
        else:
            tasks = [self._extract_text(filename, i + 1, image) for i, image in enumerate(images)]

        logger.info(f"Extracting text from PDF: {filename}, total pages: {len(tasks)}")
        await asyncio.gather(*tasks)
        return len(tasks)

    def process_pdf(self, filename: str, page_number: Optional[int] = None) -> int:
        logger.info(f"Starting complete PDF processing: {filename}")

        max_page_number = asyncio.run(self._extract_text_from_pdf(filename, page_number))

        logger.info(f"Completed complete PDF processing: {filename}")

        return max_page_number
