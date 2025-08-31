import base64
import io
import pathlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_google_genai import ChatGoogleGenerativeAI
from PIL import Image

from bookcast.config import GEMINI_API_KEY
from bookcast.entities import Chapter, ChapterStatus, Project, ProjectStatus
from bookcast.services import file_service, ocr_service
from bookcast.services.ocr_service import CalibrationChain, OCRAgent, OCRChain, OCRService


@pytest.fixture
def llm():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01)


def test_ocr_chain(llm):
    ocr_chain = OCRChain(llm)
    assert ocr_chain


def test_calibration_chain(llm):
    calibration_chain = CalibrationChain(llm)
    assert calibration_chain


def test_ocr_agent(llm):
    agent = OCRAgent(llm)
    assert agent


class TestOCRServiceIntegration:
    @pytest.mark.integration
    @patch.object(ocr_service, "OCRAgent")
    @patch.object(file_service.OCRImageFileService, "download_from_gcs")
    async def test_process(self, mock_download_from_gcs, mock_agent_class):
        project = Project(id=1, filename="test_sample.pdf", status=ProjectStatus.start_ocr)
        chapters = [
            Chapter(id=1, project_id=1, chapter_number=1, start_page=1, end_page=3, status=ChapterStatus.start_ocr),
            Chapter(id=2, project_id=1, chapter_number=2, start_page=4, end_page=5, status=ChapterStatus.start_ocr),
        ]

        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.run.return_value = "Extracted text from page"

        mock_chapter_service = MagicMock()
        ocr_service_instance = OCRService(mock_chapter_service)

        test_file_path = pathlib.Path("tests/resources/test_sample.pdf")
        mock_download_from_gcs.return_value = test_file_path

        await ocr_service_instance.process(project, chapters)

        # OCRAgent should be instantiated for each page
        assert mock_agent_class.call_count == 3
        assert mock_agent.run.call_count == 3
        assert mock_chapter_service.update.call_count == 2

    def test_image_to_base64_png(self):
        test_image = Image.new("RGB", (100, 100), color="red")

        base64_result = OCRService.image_to_base64_png(test_image)

        assert isinstance(base64_result, str)
        assert len(base64_result) > 0

        decoded_data = base64.b64decode(base64_result)
        decoded_image = Image.open(io.BytesIO(decoded_data))
        assert decoded_image.size == (100, 100)
