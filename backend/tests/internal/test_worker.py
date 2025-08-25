from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from bookcast.dependencies import get_chapter_service, get_project_service
from bookcast.entities import (
    Chapter,
    ChapterStatus,
    OCRWorkerResult,
    Project,
    ProjectStatus,
    TTSWorkerResult,
)
from bookcast.internal import worker
from bookcast.main import app
from bookcast.services.chapter_service import ChapterService
from bookcast.services.project_service import ProjectService


def create_mock_project_service():
    return MagicMock(spec=ProjectService)


def create_mock_chapter_service():
    return MagicMock(spec=ChapterService)


@pytest.fixture
def client_with_mock():
    project_service = create_mock_project_service()
    chapter_service = create_mock_chapter_service()

    project_service.find_project.return_value = Project(id=1, filename="test.pdf", status=ProjectStatus.not_started)

    chapter_service.select_chapter_by_project_id.return_value = [
        Chapter(
            id=1,
            project_id=1,
            chapter_number=1,
            start_page=1,
            end_page=10,
            extracted_text="",
            script="",
            script_file_count=2,
            status=ChapterStatus.not_started,
        ),
        Chapter(
            id=2,
            project_id=1,
            chapter_number=2,
            start_page=11,
            end_page=20,
            extracted_text="",
            script="",
            script_file_count=3,
            status=ChapterStatus.not_started,
        ),
    ]

    app.dependency_overrides[get_project_service] = lambda: project_service
    app.dependency_overrides[get_chapter_service] = lambda: chapter_service

    client = TestClient(app)
    yield client, project_service, chapter_service

    app.dependency_overrides.clear()


class TestStartOCR:
    @patch.object(worker, "invoke_task")
    @patch.object(worker, "ocr_service")
    def test_start_ocr_success(self, ocr_service, invoke_task, client_with_mock):
        client, project_service, chapter_service = client_with_mock

        ocr_service.process = AsyncMock(
            return_value=[
                OCRWorkerResult(chapter_id=1, page_number=1, extracted_text="Chapter 1 page 1 text"),
                OCRWorkerResult(chapter_id=1, page_number=2, extracted_text="Chapter 1 page 2 text"),
                OCRWorkerResult(chapter_id=2, page_number=11, extracted_text="Chapter 2 page 11 text"),
            ]
        )

        response = client.post("/internal/api/v1/workers/start_ocr", json={"project_id": 1})

        assert response.status_code == 200
        assert response.json() == {"status": 200}

        project_service.find_project.assert_called_once_with(1)
        chapter_service.select_chapter_by_project_id.assert_called_once_with(1)
        ocr_service.process.assert_called_once()
        project_service.update_project_status.assert_called()
        chapter_service.update_chapter_extracted_text.assert_called_once()
        invoke_task.assert_called_once_with(1, "start_script_writing", "bookcast-worker")


class TestStartScriptWriting:
    @patch.object(worker, "invoke_task")
    @patch.object(worker, "ScriptWritingService")
    def test_start_script_writing_success(self, mock_script_service_class, invoke_task, client_with_mock):
        client, project_service, chapter_service = client_with_mock

        project_service.find_project.return_value.status = ProjectStatus.ocr_completed

        # Mock the ScriptWritingService instance
        mock_script_service_instance = AsyncMock()
        mock_script_service_class.return_value = mock_script_service_instance

        response = client.post("/internal/api/v1/workers/start_script_writing", json={"project_id": 1})

        assert response.status_code == 200
        assert response.json() == {"status": 200}

        project_service.find_project.assert_called_once_with(1)
        chapter_service.select_chapter_by_project_id.assert_called_once_with(1)
        mock_script_service_instance.process.assert_called_once()
        project_service.update_project_status.assert_called()
        invoke_task.assert_called_once_with(1, "start_tts", "bookcast-tts-worker")


class TestStartTTS:
    @patch.object(worker, "invoke_task")
    @patch.object(worker, "tts_service")
    def test_start_tts_success(self, tts_service, invoke_task, client_with_mock):
        client, project_service, chapter_service = client_with_mock

        project_service.find_project.return_value.status = ProjectStatus.writing_script_completed

        tts_service.generate_audio = AsyncMock(
            return_value=[
                TTSWorkerResult(chapter_id=1, index=3),
                TTSWorkerResult(chapter_id=2, index=2),
            ]
        )

        response = client.post("/internal/api/v1/workers/start_tts", json={"project_id": 1})

        assert response.status_code == 200
        assert response.json() == {"status": 200}

        project_service.find_project.assert_called_once_with(1)
        chapter_service.select_chapter_by_project_id.assert_called_once_with(1)
        tts_service.generate_audio.assert_called_once()
        project_service.update_project_status.assert_called()
        chapter_service.update_chapter_script_file_count.assert_called_once()
        invoke_task.assert_called_once_with(1, "start_creating_audio", "bookcast-worker")


class TestStartCreatingAudio:
    @patch.object(worker, "audio_service")
    def test_start_creating_audio_success(self, audio_service, client_with_mock):
        client, project_service, chapter_service = client_with_mock

        project_service.find_project.return_value.status = ProjectStatus.tts_completed

        response = client.post("/internal/api/v1/workers/start_creating_audio", json={"project_id": 1})

        assert response.status_code == 200
        assert response.json() == {"status": 200}

        project_service.find_project.assert_called_once_with(1)
        chapter_service.select_chapter_by_project_id.assert_called_once_with(1)
        audio_service.generate_audio.assert_called_once()
        project_service.update_project_status.assert_called()
        chapter_service.update_chapters_status.assert_called()
