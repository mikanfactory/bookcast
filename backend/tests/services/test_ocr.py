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
from bookcast.services.ocr_service import OCRService


@pytest.fixture
def llm():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01)


@pytest.mark.asyncio
@patch.object(ocr_service, "ocr_workflow")
async def test_ocr_service_extract(mock_ocr_workflow):
    mock_ocr_workflow.ainvoke = AsyncMock(return_value="Extracted text")

    mock_chapter_service = MagicMock()
    service = OCRService(mock_chapter_service)

    test_image = Image.new("RGB", (100, 100), color="red")

    result = await service._extract(test_image)

    assert result == "Extracted text"
    assert mock_ocr_workflow.ainvoke.called

    mock_ocr_workflow.ainvoke.assert_called_once()
    args, kwargs = mock_ocr_workflow.ainvoke.call_args
    assert kwargs["config"]["run_name"] == "OCRAgent"


class TestOCRServiceIntegration:
    @pytest.mark.integration
    @patch.object(ocr_service, "ocr_workflow")
    @patch.object(file_service.OCRImageFileService, "download_from_gcs")
    async def test_process(self, mock_download_from_gcs, mock_ocr_workflow):
        project = Project(id=1, filename="test_sample.pdf", status=ProjectStatus.start_ocr)
        chapters = [
            Chapter(id=1, project_id=1, chapter_number=1, start_page=1, end_page=3, status=ChapterStatus.start_ocr),
            Chapter(id=2, project_id=1, chapter_number=2, start_page=4, end_page=5, status=ChapterStatus.start_ocr),
        ]

        mock_ocr_workflow.ainvoke = AsyncMock(return_value="Extracted text from page")

        mock_chapter_service = MagicMock()
        ocr_service_instance = OCRService(mock_chapter_service)

        test_file_path = pathlib.Path("tests/resources/test_sample.pdf")
        mock_download_from_gcs.return_value = test_file_path

        await ocr_service_instance.process(project, chapters)

        assert mock_ocr_workflow.ainvoke.call_count == 3
        assert mock_chapter_service.update.call_count == 2

    def test_image_to_base64_png(self):
        test_image = Image.new("RGB", (100, 100), color="red")

        base64_result = OCRService.image_to_base64_png(test_image)

        assert isinstance(base64_result, str)
        assert len(base64_result) > 0

        decoded_data = base64.b64decode(base64_result)
        decoded_image = Image.open(io.BytesIO(decoded_data))
        assert decoded_image.size == (100, 100)
