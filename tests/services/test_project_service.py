from unittest.mock import MagicMock

import pytest

from bookcast.entities import Project, ProjectStatus
from bookcast.services.project import ProjectService


def create_mock_project_service():
    mock_project_repo = MagicMock()
    mock_chapter_repo = MagicMock()
    return ProjectService(mock_project_repo, mock_chapter_repo)


@pytest.fixture
def service_with_mock():
    mock_service = create_mock_project_service()

    mock_service.project_repo.select_all.return_value = [
        Project(id=1, filename="test1.pdf", max_page_number=10, status=ProjectStatus.not_started),
        Project(id=2, filename="test2.pdf", max_page_number=20, status=ProjectStatus.ocr_completed),
    ]
    mock_service.project_repo.find.return_value = Project(
        id=1, filename="test1.pdf", max_page_number=10, status=ProjectStatus.not_started
    )

    return mock_service


@pytest.fixture
def service_with_empty_mock():
    mock_service = create_mock_project_service()
    mock_service.project_repo.select_all.return_value = []
    mock_service.project_repo.find.return_value = None

    return mock_service


class TestFetchAllProjects:
    def test_fetch_all_projects(self, service_with_mock):
        result = service_with_mock.fetch_all_projects()

        assert len(result) == 2
        assert isinstance(result[0], Project)

        service_with_mock.project_repo.select_all.assert_called_once()

    def test_fetch_all_projects_empty(self, service_with_empty_mock):
        result = service_with_empty_mock.fetch_all_projects()

        assert len(result) == 0

        service_with_empty_mock.project_repo.select_all.assert_called_once()


class TestFindProject:
    def test_find_project(self, service_with_mock):
        result = service_with_mock.find_project(1)

        assert result
        assert isinstance(result, Project)

        service_with_mock.project_repo.find.assert_called_once_with(1)

    def test_find_project_not_found(self, service_with_empty_mock):
        result = service_with_empty_mock.find_project(999)

        assert result is None

        service_with_empty_mock.project_repo.find.assert_called_once_with(999)


class TestUpdateProjectStatus:
    def test_update_project_status(self, service_with_mock):
        project = Project(id=1, filename="test.pdf", max_page_number=10, status=ProjectStatus.not_started)
        new_status = ProjectStatus.start_ocr

        service_with_mock.update_project_status(project, new_status)

        assert project.status == new_status
        service_with_mock.project_repo.update.assert_called_once_with(project)


class TestCreateProject:
    @pytest.mark.skip("Skipping test_create_project as it is not implemented yet")
    def test_create_project(self, service_with_mock):
        filename = "test.pdf"
        file_mock = MagicMock()

        result = service_with_mock.create_project(filename, file_mock)

        assert result is None
