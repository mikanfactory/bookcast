from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from bookcast.dependencies import get_chapter_service
from bookcast.entities import Chapter, ChapterStatus
from bookcast.main import app
from bookcast.services.chapter_service import ChapterService


def create_mock_chapter_service():
    mock_chapter_repo = MagicMock()
    mock_project_repo = MagicMock()
    return ChapterService(mock_chapter_repo, mock_project_repo)


@pytest.fixture
def client_with_mock():
    chapter_service = create_mock_chapter_service()

    chapter_service.chapter_repo.select_chapter_by_project_id.return_value = [
        Chapter(
            id=1,
            project_id=1,
            chapter_number=1,
            start_page=1,
            end_page=10,
            extracted_text="Chapter 1 content",
            script="Chapter 1 script",
            script_file_count=0,
            status=ChapterStatus.not_started,
        ),
        Chapter(
            id=2,
            project_id=1,
            chapter_number=2,
            start_page=11,
            end_page=20,
            extracted_text="Chapter 2 content",
            script="Chapter 2 script",
            script_file_count=1,
            status=ChapterStatus.ocr_completed,
        ),
    ]

    chapter_service.chapter_repo.bulk_create.return_value = [
        Chapter(
            id=1,
            project_id=1,
            chapter_number=1,
            start_page=1,
            end_page=10,
            status=ChapterStatus.not_started,
        ),
        Chapter(
            id=2,
            project_id=1,
            chapter_number=2,
            start_page=11,
            end_page=20,
            status=ChapterStatus.not_started,
        ),
    ]

    app.dependency_overrides[get_chapter_service] = lambda: chapter_service

    client = TestClient(app)
    yield client, chapter_service

    app.dependency_overrides.clear()


class TestCreateChapters:
    @patch("bookcast.routers.chapter.invoke_task")
    def test_create_chapters(self, mock_invoke_task, client_with_mock):
        client, chapter_service = client_with_mock
        mock_invoke_task.return_value = {"task_id": "mock-task-id"}

        json_value = {
            "project_id": 1,
            "chapters": [
                {"chapter_number": 1, "start_page": 1, "end_page": 10},
                {"chapter_number": 2, "start_page": 11, "end_page": 20},
            ],
        }

        response = client.post("/api/v1/chapters/create_chapters", json=json_value)
        assert response.status_code == 200

        mock_invoke_task.assert_called_once_with(1, "start_ocr", "bookcast-worker")
        chapter_service.chapter_repo.bulk_create.assert_called_once()
