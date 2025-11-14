import asyncio
import base64
import io
import pathlib
from logging import getLogger

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.config import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.func import entrypoint, task
from pdf2image import convert_from_path
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

from bookcast.config import GEMINI_API_KEY
from bookcast.entities import Project
from bookcast.services.file_service import OCRImageFileService

logger = getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"


class ChapterStartPageNumber(BaseModel):
    page_number: int
    title: str


class OCRResult(BaseModel):
    chapter_pages: list[ChapterStartPageNumber] = Field(default=[], description="章のタイトルとページ番号")
    is_table_of_contents_page: bool = Field(..., description="目次を含むページか否か")


class OCRWorkflowInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    base64_image: str = Field(..., description="画像")
    llm: ChatGoogleGenerativeAI


@task
async def execute_ocr(llm, base64_image: str) -> OCRResult:
    prompt_text = """
あなたは書籍の目次のOCRを行うAIです。
与えられた画像に目次が含まれていた場合のみ、章のタイトルとページ番号を読み取ってください。
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
                        "data": base64_image,
                        "mime_type": "image/png",
                    },
                ],
            )
        ]
    )

    chain = message | llm.with_structured_output(OCRResult)
    result: OCRResult = await chain.ainvoke({})
    return result


@entrypoint()
async def ocr_workflow(inputs: OCRWorkflowInput) -> OCRResult:
    return await execute_ocr(inputs.llm, inputs.base64_image)


class Page(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    page_number: int
    image: Image.Image


class ChapterSearchService:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(10)

    @staticmethod
    def image_to_base64_png(image: Image.Image) -> str:
        with io.BytesIO() as buf:
            image.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()

    async def _extract(self, page: Page) -> OCRResult:
        async with self.semaphore:
            base64_image = self.image_to_base64_png(page.image)
            llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY, temperature=0.01)
            response = await ocr_workflow.ainvoke(
                OCRWorkflowInput(
                    base64_image=base64_image,
                    llm=llm,
                ),
                config=RunnableConfig(run_name="OCRAgent"),
            )

        return response

    async def _extract_table_of_contents(self, pages: list[Page]) -> list[ChapterStartPageNumber]:
        tasks = []
        for page in pages:
            tasks.append(self._extract(page))

        logger.info("Starting OCR for the first 20 pages...")
        results: list[OCRResult] = await asyncio.gather(*tasks)

        chapter_pages = []
        for r in results:
            if r.is_table_of_contents_page:
                chapter_pages.extend(r.chapter_pages)
        return chapter_pages

    async def _process(self, book_path: pathlib.Path) -> list[ChapterStartPageNumber]:
        images = convert_from_path(book_path, first_page=0, last_page=20, dpi=150, fmt="RGB")
        pages = [Page(page_number=1, image=images[i]) for i in range(len(images))]
        return await self._extract_table_of_contents(pages)

    async def process(self, project: Project) -> list[ChapterStartPageNumber]:
        logger.info(f"Starting OCR: {project.filename}")

        book_path = OCRImageFileService.download_from_gcs(project.filename)
        result = await self._process(book_path)

        logger.info(f"Completed OCR: {project.filename}")
        return result
