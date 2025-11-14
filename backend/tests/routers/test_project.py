from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from bookcast.dependencies import get_project_service
from bookcast.entities import Project, ProjectStatus
from bookcast.main import app
from bookcast.services import file_service
from bookcast.services.chapter_search_service import ChapterStartPageNumber
from bookcast.services.project_service import ProjectService


def create_mock_project_service():
    mock_project_repo = MagicMock()
    mock_chapter_repo = MagicMock()
    return ProjectService(mock_project_repo, mock_chapter_repo)


@pytest.fixture
def client_with_mock():
    project_service = create_mock_project_service()

    project_service.project_repo.select_all.return_value = [
        Project(id=1, filename="test1.pdf", status=ProjectStatus.not_started),
        Project(id=2, filename="test2.pdf", status=ProjectStatus.ocr_completed),
    ]
    project_service.project_repo.find.return_value = Project(
        id=1, filename="test1.pdf", status=ProjectStatus.not_started
    )
    project_service.project_repo.create.return_value = Project(
        id=1, filename="test.pdf", status=ProjectStatus.not_started
    )

    app.dependency_overrides[get_project_service] = lambda: project_service

    client = TestClient(app)
    yield client, project_service

    app.dependency_overrides.clear()


@pytest.fixture
def client_with_empty_mock():
    project_service = create_mock_project_service()
    project_service.project_repo.select_all.return_value = []
    project_service.project_repo.find.return_value = None
    app.dependency_overrides[get_project_service] = lambda: project_service

    client = TestClient(app)
    yield client, project_service

    app.dependency_overrides.clear()


class TestIndex:
    def test_index(self, client_with_mock):
        client, project_service = client_with_mock

        response = client.get("/api/v1/projects/")
        assert response.status_code == 200

        resp = response.json()
        assert len(resp) == 2
        assert resp[0]["id"] == 1
        assert resp[0]["filename"] == "test1.pdf"

        project_service.project_repo.select_all.assert_called_once()

    def test_index_with_empty_projects(self, client_with_empty_mock):
        client, project_service = client_with_empty_mock

        response = client.get("/api/v1/projects/")
        assert response.status_code == 200

        resp = response.json()
        assert len(resp) == 0

        project_service.project_repo.select_all.assert_called_once()


class TestShow:
    def test_show(self, client_with_mock):
        client, project_service = client_with_mock

        response = client.get("/api/v1/projects/1")
        assert response.status_code == 200

        resp = response.json()
        assert resp["id"] == 1
        assert resp["filename"] == "test1.pdf"

        project_service.project_repo.find.assert_called_once_with(1)

    def test_show_not_found(self, client_with_empty_mock):
        client, project_service = client_with_empty_mock

        response = client.get("/api/v1/projects/999")
        assert response.status_code == 404

        project_service.project_repo.find.assert_called_once_with(999)


class TestUploadFile:
    @patch.object(file_service.OCRImageFileService, "write", return_value="/tmp/test.pdf")
    @patch.object(file_service.OCRImageFileService, "upload_gcs_from_file")
    def test_upload_file(self, mock_upload, mock_write, client_with_mock):
        client, project_service = client_with_mock

        file = b"mock file content"
        response = client.post("/api/v1/projects/upload_file", files={"file": ("test.pdf", file)})

        assert response.status_code == 200
        resp = response.json()
        assert resp["filename"] == "test.pdf"

        project_service.project_repo.create.assert_called_once()
        mock_upload.assert_called_once()

    def test_upload_file_error(self, client_with_mock):
        client, project_service = client_with_mock

        response = client.post("/api/v1/projects/upload_file", files={})
        assert response.status_code == 422  # Unprocessable Entity


def mock_zip_generator():
    yield b"fake zip content"


class TestDownloadProject:
    @patch.object(ProjectService, "create_download_archive", return_value=(mock_zip_generator(), "test_audio.zip"))
    def test_download_project_success(self, mock_create_archive, client_with_mock):
        client, project_service = client_with_mock

        response = client.get("/api/v1/projects/1/download")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert "attachment" in response.headers["content-disposition"]
        assert "test_audio.zip" in response.headers["content-disposition"]
        assert response.content == b"fake zip content"

        expected_project = Project(id=1, filename="test1.pdf", status=ProjectStatus.not_started)
        mock_create_archive.assert_called_once_with(expected_project)


class TestExtractTableOfContents:
    @patch("bookcast.routers.project.ChapterSearchService")
    def test_extract_table_of_contents_success(self, mock_chapter_search_service_class, client_with_mock):
        client, project_service = client_with_mock

        mock_chapter_pages = [
            ChapterStartPageNumber(page_number=1, title="第1章 はじめに"),
            ChapterStartPageNumber(page_number=5, title="第2章 基本概念"),
            ChapterStartPageNumber(page_number=10, title="第3章 応用"),
        ]

        mock_service_instance = MagicMock()
        mock_service_instance.process = AsyncMock(return_value=mock_chapter_pages)
        mock_chapter_search_service_class.return_value = mock_service_instance

        response = client.post("/api/v1/projects/1/extract_table_of_contents")

        assert response.status_code == 200
        resp = response.json()
        assert len(resp) == 3
        assert resp[0]["page_number"] == 1
        assert resp[0]["title"] == "第1章 はじめに"
        assert resp[1]["page_number"] == 5
        assert resp[1]["title"] == "第2章 基本概念"
        assert resp[2]["page_number"] == 10
        assert resp[2]["title"] == "第3章 応用"

        project_service.project_repo.find.assert_called_once_with(1)
        expected_project = Project(id=1, filename="test1.pdf", status=ProjectStatus.not_started)
        mock_service_instance.process.assert_called_once_with(expected_project)

    def test_extract_table_of_contents_project_not_found(self, client_with_empty_mock):
        client, project_service = client_with_empty_mock

        response = client.post("/api/v1/projects/999/extract_table_of_contents")

        assert response.status_code == 404
        resp = response.json()
        assert resp["detail"]["success"] is False
        assert resp["detail"]["message"] == "Project not found"
        assert resp["detail"]["error_code"] == "PROJECT_NOT_FOUND"

        project_service.project_repo.find.assert_called_once_with(999)
