from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from bookcast.dependencies import get_project_service
from bookcast.entities import Project, ProjectStatus
from bookcast.main import app
from bookcast.services.project import ProjectService


def create_mock_project_service():
    mock_project_repo = MagicMock()
    mock_chapter_repo = MagicMock()
    return ProjectService(mock_project_repo, mock_chapter_repo)


@pytest.fixture
def client_with_mock():
    project_service = create_mock_project_service()

    project_service.project_repo.select_all.return_value = [
        Project(id=1, filename="test1.pdf", max_page_number=10, status=ProjectStatus.not_started),
        Project(id=2, filename="test2.pdf", max_page_number=20, status=ProjectStatus.ocr_completed),
    ]
    project_service.project_repo.find.return_value = Project(
        id=1, filename="test1.pdf", max_page_number=10, status=ProjectStatus.not_started
    )
    project_service.project_repo.create.return_value = Project(
        id=1, filename="test.pdf", max_page_number=5, status=ProjectStatus.not_started
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
    def test_upload_file(self, client_with_mock):
        client, project_service = client_with_mock

        with (
            patch("bookcast.services.project.convert_from_path") as mock_convert,
            patch("bookcast.services.file.OCRImageFileService.write") as mock_write,
            patch("bookcast.services.file.OCRImageFileService.upload_gcs_from_file") as mock_upload,
        ):
            mock_convert.return_value = [MagicMock() for _ in range(5)]
            mock_write.return_value = "/tmp/test.pdf"

            file = b"mock file content"
            response = client.post("/api/v1/projects/upload_file", files={"file": ("test.pdf", file)})

            assert response.status_code == 200
            resp = response.json()
            assert resp["filename"] == "test.pdf"
            assert resp["max_page_number"] == 5

            project_service.project_repo.create.assert_called_once()
            mock_upload.assert_called_once()

    def test_upload_file_error(self, client_with_mock):
        client, project_service = client_with_mock

        response = client.post("/api/v1/projects/upload_file", files={})
        assert response.status_code == 422  # Unprocessable Entity
