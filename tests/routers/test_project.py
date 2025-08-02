from unittest.mock import MagicMock

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
    mock_service = create_mock_project_service()

    mock_service.project_repo.select_all.return_value = [
        Project(id=1, filename="test1.pdf", max_page_number=10, status=ProjectStatus.not_started),
        Project(id=2, filename="test2.pdf", max_page_number=20, status=ProjectStatus.ocr_completed),
    ]
    mock_service.project_repo.find.return_value = Project(
        id=1, filename="test1.pdf", max_page_number=10, status=ProjectStatus.not_started
    )

    app.dependency_overrides[get_project_service] = lambda: mock_service

    client = TestClient(app)
    yield client, mock_service

    app.dependency_overrides.clear()


@pytest.fixture
def client_with_empty_mock():
    mock_service = create_mock_project_service()
    mock_service.project_repo.select_all.return_value = []
    mock_service.project_repo.find.return_value = None
    app.dependency_overrides[get_project_service] = lambda: mock_service

    client = TestClient(app)
    yield client, mock_service

    app.dependency_overrides.clear()


class TestIndex:
    def test_index(self, client_with_mock):
        client, mock_service = client_with_mock

        response = client.get("/api/v1/projects/")
        assert response.status_code == 200

        resp = response.json()
        assert len(resp) == 2
        assert resp[0]["id"] == 1
        assert resp[0]["filename"] == "test1.pdf"

        mock_service.project_repo.select_all.assert_called_once()

    def test_index_with_empty_projects(self, client_with_empty_mock):
        client, mock_service = client_with_empty_mock

        response = client.get("/api/v1/projects/")
        assert response.status_code == 200

        resp = response.json()
        assert len(resp) == 0

        mock_service.project_repo.select_all.assert_called_once()


class TestShow:
    def test_show(self, client_with_mock):
        client, mock_service = client_with_mock

        response = client.get("/api/v1/projects/1")
        assert response.status_code == 200

        resp = response.json()
        assert resp["id"] == 1
        assert resp["filename"] == "test1.pdf"

        mock_service.project_repo.find.assert_called_once_with(1)

    def test_show_not_found(self, client_with_empty_mock):
        client, mock_service = client_with_empty_mock

        response = client.get("/api/v1/projects/999")
        assert response.status_code == 404

        mock_service.project_repo.find.assert_called_once_with(999)
