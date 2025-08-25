import base64
import io
import pathlib
from unittest.mock import AsyncMock, patch

import pytest
from langchain_google_genai import ChatGoogleGenerativeAI
from PIL import Image

from bookcast.config import GEMINI_API_KEY
from bookcast.entities import Chapter, ChapterStatus, OCRWorkerResult, Project, ProjectStatus
from bookcast.services.ocr_service import OCRExecutor, OCROrchestrator, OCRResultEditor, OCRService


@pytest.fixture
def llm():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01)


def test_ocr_executor(llm):
    ocr_executor = OCRExecutor(llm)
    assert ocr_executor


def test_ocr_result_editor(llm):
    ocr_editor = OCRResultEditor(llm)
    assert ocr_editor


def test_ocr_orchestrator(llm):
    orchestrator = OCROrchestrator(llm)
    assert orchestrator


class TestOCRServiceIntegration:
    @pytest.mark.integration
    @patch("bookcast.services.ocr_service.OCROrchestrator")
    async def test_process(self, mock_orchestrator_class):
        project = Project(id=1, filename="test_sample.pdf", status=ProjectStatus.start_ocr)
        chapters = [
            Chapter(id=1, project_id=1, chapter_number=1, start_page=1, end_page=3, status=ChapterStatus.start_ocr)
        ]

        mock_orchestrator = AsyncMock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.run.return_value = "Extracted text from page"

        ocr_service = OCRService()

        test_file_path = pathlib.Path("tests/resources/test_sample.pdf")
        with patch("bookcast.services.ocr_service.OCRImageFileService.download_from_gcs", return_value=test_file_path):
            results = await ocr_service.process(project, chapters)

        assert isinstance(results, list)
        assert len(results) > 0

        for result in results:
            assert isinstance(result, OCRWorkerResult)
            assert result.extracted_text == "Extracted text from page"

        assert mock_orchestrator.run.call_count == len(results)

    def test_image_to_base64_png(self):
        test_image = Image.new("RGB", (100, 100), color="red")

        base64_result = OCRService.image_to_base64_png(test_image)

        assert isinstance(base64_result, str)
        assert len(base64_result) > 0

        decoded_data = base64.b64decode(base64_result)
        decoded_image = Image.open(io.BytesIO(decoded_data))
        assert decoded_image.size == (100, 100)
