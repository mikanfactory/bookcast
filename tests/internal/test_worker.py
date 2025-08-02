from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from bookcast.dependencies import get_chapter_service, get_project_service
from bookcast.entities import (
    Chapter,
    ChapterStatus,
    OCRWorkerResult,
    Project,
    ProjectStatus,
    ScriptWritingWorkerResult,
    TTSWorkerResult,
)
from bookcast.main import app
from bookcast.services.chapter import ChapterService
from bookcast.services.project import ProjectService


def create_mock_project_service():
    return MagicMock(spec=ProjectService)


def create_mock_chapter_service():
    return MagicMock(spec=ChapterService)


@pytest.fixture
def client_with_mock():
    mock_project_service = create_mock_project_service()
    mock_chapter_service = create_mock_chapter_service()

    mock_project_service.find_project.return_value = Project(
        id=1, filename="test.pdf", max_page_number=20, status=ProjectStatus.not_started
    )

    mock_chapter_service.select_chapters.return_value = [
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

    app.dependency_overrides[get_project_service] = lambda: mock_project_service
    app.dependency_overrides[get_chapter_service] = lambda: mock_chapter_service

    client = TestClient(app)
    yield client, mock_project_service, mock_chapter_service

    app.dependency_overrides.clear()


class TestStartOCR:
    @patch("bookcast.internal.worker.ocr_service")
    def test_start_ocr_success(self, mock_ocr_service, client_with_mock):
        client, mock_project_service, mock_chapter_service = client_with_mock

        mock_ocr_service.process.return_value = [
            OCRWorkerResult(chapter_id=1, page_number=1, extracted_text="Chapter 1 page 1 text"),
            OCRWorkerResult(chapter_id=1, page_number=2, extracted_text="Chapter 1 page 2 text"),
            OCRWorkerResult(chapter_id=2, page_number=11, extracted_text="Chapter 2 page 11 text"),
        ]

        response = client.post("/internal/api/v1/workers/start_ocr/1")

        assert response.status_code == 200
        assert response.json() == {"status": 200}

        mock_project_service.find_project.assert_called_once_with(1)
        mock_chapter_service.select_chapters.assert_called_once_with(1)
        mock_ocr_service.process.assert_called_once()
        mock_project_service.update_project_status.assert_called()
        mock_chapter_service.update_chapter_extracted_text.assert_called_once()


class TestStartScriptWriting:
    @patch("bookcast.internal.worker.script_writing_service")
    def test_start_script_writing_success(self, mock_script_service, client_with_mock):
        client, mock_project_service, mock_chapter_service = client_with_mock

        mock_project_service.find_project.return_value.status = ProjectStatus.ocr_completed

        mock_script_service.process.return_value = [
            ScriptWritingWorkerResult(chapter_id=1, script="Generated script for chapter 1"),
            ScriptWritingWorkerResult(chapter_id=2, script="Generated script for chapter 2"),
        ]

        response = client.post("/internal/api/v1/workers/start_script_writing/1")

        assert response.status_code == 200
        assert response.json() == {"status": 200}

        mock_project_service.find_project.assert_called_once_with(1)
        mock_chapter_service.select_chapters.assert_called_once_with(1)
        mock_script_service.process.assert_called_once()
        mock_project_service.update_project_status.assert_called()
        mock_chapter_service.update_chapter_script.assert_called_once()


class TestStartTTS:
    @patch("bookcast.internal.worker.tts_service")
    def test_start_tts_success(self, mock_tts_service, client_with_mock):
        client, mock_project_service, mock_chapter_service = client_with_mock

        mock_project_service.find_project.return_value.status = ProjectStatus.writing_script_completed

        mock_tts_service.generate_audio.return_value = [
            TTSWorkerResult(chapter_id=1, index=3),
            TTSWorkerResult(chapter_id=2, index=2),
        ]

        response = client.post("/internal/api/v1/workers/start_tts/1")

        assert response.status_code == 200
        assert response.json() == {"status": 200}

        mock_project_service.find_project.assert_called_once_with(1)
        mock_chapter_service.select_chapters.assert_called_once_with(1)
        mock_tts_service.generate_audio.assert_called_once()
        mock_project_service.update_project_status.assert_called()
        mock_chapter_service.update_chapter_script_file_count.assert_called_once()


class TestStartCreatingAudio:
    @patch("bookcast.internal.worker.audio_service")
    @patch("bookcast.internal.worker.TTSFileService")
    def test_start_creating_audio_success(self, mock_file_service, mock_audio_service, client_with_mock):
        client, mock_project_service, mock_chapter_service = client_with_mock

        mock_project_service.find_project.return_value.status = ProjectStatus.tts_completed

        response = client.post("/internal/api/v1/workers/start_creating_audio/1")

        assert response.status_code == 200
        assert response.json() == {"status": 200}

        mock_project_service.find_project.assert_called_once_with(1)
        mock_chapter_service.select_chapters.assert_called_once_with(1)
        mock_file_service.download_from_gcs.assert_called()
        mock_audio_service.generate_audio.assert_called_once()
        mock_project_service.update_project_status.assert_called()
        mock_chapter_service.update_chapters_status.assert_called()
