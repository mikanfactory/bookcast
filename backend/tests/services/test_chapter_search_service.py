import pathlib
from unittest.mock import AsyncMock, patch

import pytest
from PIL import Image

from bookcast.entities import Project, ProjectStatus
from bookcast.services import chapter_search_service
from bookcast.services.chapter_search_service import ChapterSearchService, ChapterStartPageNumber, OCRResult


@pytest.fixture
def mock_project():
    return Project(id=1, filename="test_sample.pdf", status=ProjectStatus.not_started)


@pytest.fixture
def mock_images():
    return [Image.new("RGB", (100, 100), color="red") for _ in range(3)]


@pytest.fixture
def mock_toc_ocr_result():
    return OCRResult(
        chapter_pages=[
            ChapterStartPageNumber(page_number=1, title="第1章 はじめに"),
            ChapterStartPageNumber(page_number=5, title="第2章 基本概念"),
        ],
        is_table_of_contents_page=True,
    )


@pytest.fixture
def mock_no_toc_ocr_result():
    return OCRResult(chapter_pages=[], is_table_of_contents_page=False)


class TestChapterSearchServiceIntegration:
    @pytest.mark.integration
    @patch.object(chapter_search_service, "convert_from_path")
    @patch.object(chapter_search_service.OCRImageFileService, "download_from_gcs")
    @patch.object(chapter_search_service, "ocr_workflow")
    async def test_process_with_table_of_contents(
        self,
        mock_ocr_workflow,
        mock_download_from_gcs,
        mock_convert_from_path,
        mock_project,
        mock_images,
        mock_toc_ocr_result,
    ):
        test_file_path = pathlib.Path("tests/resources/test_sample.pdf")
        mock_download_from_gcs.return_value = test_file_path
        mock_convert_from_path.return_value = mock_images

        mock_ocr_workflow.ainvoke = AsyncMock()
        mock_ocr_workflow.ainvoke.return_value = mock_toc_ocr_result

        service = ChapterSearchService()
        results = await service.process(mock_project)

        assert len(results) == 6  # 3枚の画像 × 2章ずつ = 6章
        assert all(isinstance(cp, ChapterStartPageNumber) for cp in results)
        # 各画像で同じOCRResultが返されるため、章が重複する
        expected_titles = ["第1章 はじめに", "第2章 基本概念"] * 3
        actual_titles = [result.title for result in results]
        assert actual_titles == expected_titles

        mock_download_from_gcs.assert_called_once_with("test_sample.pdf")
        mock_convert_from_path.assert_called_once_with(test_file_path, first_page=0, last_page=20, dpi=150, fmt="RGB")
        assert mock_ocr_workflow.ainvoke.call_count == 3

    @pytest.mark.integration
    @patch.object(chapter_search_service, "convert_from_path")
    @patch.object(chapter_search_service.OCRImageFileService, "download_from_gcs")
    @patch.object(chapter_search_service, "ocr_workflow")
    async def test_process_no_table_of_contents(
        self,
        mock_ocr_workflow,
        mock_download_from_gcs,
        mock_convert_from_path,
        mock_project,
        mock_images,
        mock_no_toc_ocr_result,
    ):
        test_file_path = pathlib.Path("tests/resources/test_sample.pdf")
        mock_download_from_gcs.return_value = test_file_path
        mock_convert_from_path.return_value = mock_images

        mock_ocr_workflow.ainvoke = AsyncMock()
        mock_ocr_workflow.ainvoke.return_value = mock_no_toc_ocr_result

        service = ChapterSearchService()
        results = await service.process(mock_project)

        assert len(results) == 0
        assert isinstance(results, list)

        mock_download_from_gcs.assert_called_once_with("test_sample.pdf")
        mock_convert_from_path.assert_called_once_with(test_file_path, first_page=0, last_page=20, dpi=150, fmt="RGB")
        assert mock_ocr_workflow.ainvoke.call_count == 3
