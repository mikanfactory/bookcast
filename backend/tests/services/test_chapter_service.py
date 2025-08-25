from unittest.mock import MagicMock

import pytest

from bookcast.entities import Chapter, ChapterStatus
from bookcast.services.chapter_service import ChapterService


def create_mock_chapter_service():
    mock_chapter_repo = MagicMock()
    mock_project_repo = MagicMock()
    return ChapterService(mock_chapter_repo, mock_project_repo)


@pytest.fixture
def chapter_service_mock():
    chapter_service = create_mock_chapter_service()

    chapter_service.chapter_repo.select_chapter_by_project_id.return_value = [
        Chapter(id=1, project_id=1, chapter_number=1, start_page=1, end_page=5, status=ChapterStatus.not_started),
        Chapter(id=2, project_id=1, chapter_number=2, start_page=6, end_page=10, status=ChapterStatus.ocr_completed),
    ]

    chapter_service.chapter_repo.bulk_create.return_value = [
        Chapter(id=3, project_id=1, chapter_number=1, start_page=1, end_page=5, status=ChapterStatus.not_started),
        Chapter(id=4, project_id=1, chapter_number=2, start_page=6, end_page=10, status=ChapterStatus.not_started),
    ]

    chapter_service.chapter_repo.update.return_value = [
        Chapter(id=3, project_id=1, chapter_number=1, start_page=1, end_page=5, status=ChapterStatus.not_started),
        Chapter(id=4, project_id=1, chapter_number=2, start_page=6, end_page=10, status=ChapterStatus.not_started),
    ]

    return chapter_service


@pytest.fixture
def service_with_empty_mock():
    chapter_service = create_mock_chapter_service()
    chapter_service.chapter_repo.select_chapter_by_project_id.return_value = []

    return chapter_service


class TestSelectChapterByProjectId:
    def test_select_chapter_by_project_id(self, chapter_service_mock):
        result = chapter_service_mock.select_chapter_by_project_id(1)

        assert len(result) == 2
        assert isinstance(result[0], Chapter)
        assert result[0].project_id == 1
        assert result[1].project_id == 1

        chapter_service_mock.chapter_repo.select_chapter_by_project_id.assert_called_once_with(1)

    def test_select_chapter_by_project_id_empty(self, service_with_empty_mock):
        result = service_with_empty_mock.select_chapter_by_project_id(999)

        assert len(result) == 0

        service_with_empty_mock.chapter_repo.select_chapter_by_project_id.assert_called_once_with(999)


class TestUpdateChaptersStatus:
    def test_update_chapters_status(self, chapter_service_mock):
        chapters = [
            Chapter(id=1, project_id=1, chapter_number=1, start_page=1, end_page=5, status=ChapterStatus.not_started),
            Chapter(id=2, project_id=1, chapter_number=2, start_page=6, end_page=10, status=ChapterStatus.not_started),
        ]
        new_status = ChapterStatus.start_ocr

        chapter_service_mock.update_chapters_status(chapters, new_status)

        assert chapters[0].status == new_status
        assert chapters[1].status == new_status
        assert chapter_service_mock.chapter_repo.update.call_count == 2


class TestCreateChapters:
    def test_create_chapters(self, chapter_service_mock):
        chapters = [
            Chapter(project_id=1, chapter_number=1, start_page=1, end_page=5),
            Chapter(project_id=1, chapter_number=2, start_page=6, end_page=10),
        ]

        result = chapter_service_mock.create_chapters(chapters)
        assert result is not None
