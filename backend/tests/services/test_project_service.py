from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from bookcast.entities import Project, ProjectStatus
from bookcast.services.project import ProjectService


def create_mock_project_service():
    mock_project_repo = MagicMock()
    mock_chapter_repo = MagicMock()
    return ProjectService(mock_project_repo, mock_chapter_repo)


@pytest.fixture
def project_service_mock():
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

    return project_service


@pytest.fixture
def project_service_with_empty_mock():
    project_service = create_mock_project_service()
    project_service.project_repo.select_all.return_value = []
    project_service.project_repo.find.return_value = None

    return project_service


class TestFetchAllProjects:
    def test_fetch_all_projects(self, project_service_mock):
        result = project_service_mock.fetch_all_projects()

        assert len(result) == 2
        assert isinstance(result[0], Project)

        project_service_mock.project_repo.select_all.assert_called_once()

    def test_fetch_all_projects_empty(self, project_service_with_empty_mock):
        result = project_service_with_empty_mock.fetch_all_projects()

        assert len(result) == 0

        project_service_with_empty_mock.project_repo.select_all.assert_called_once()


class TestFindProject:
    def test_find_project(self, project_service_mock):
        result = project_service_mock.find_project(1)

        assert result
        assert isinstance(result, Project)

        project_service_mock.project_repo.find.assert_called_once_with(1)

    def test_find_project_not_found(self, project_service_with_empty_mock):
        result = project_service_with_empty_mock.find_project(999)

        assert result is None

        project_service_with_empty_mock.project_repo.find.assert_called_once_with(999)


class TestUpdateProjectStatus:
    def test_update_project_status(self, project_service_mock):
        project = Project(id=1, filename="test.pdf", max_page_number=10, status=ProjectStatus.not_started)
        new_status = ProjectStatus.start_ocr

        project_service_mock.update_project_status(project, new_status)

        assert project.status == new_status
        project_service_mock.project_repo.update.assert_called_once_with(project)


class TestCreateProject:
    def test_create_project(self, project_service_mock):
        filename = "test.pdf"
        file_content = b"mock file content"
        file = BytesIO(file_content)

        with (
            patch("bookcast.services.project.convert_from_path") as mock_convert,
            patch("bookcast.services.file.OCRImageFileService.write") as mock_write,
            patch("bookcast.services.file.OCRImageFileService.upload_gcs_from_file") as mock_upload,
        ):
            mock_convert.return_value = [MagicMock() for _ in range(5)]
            mock_write.return_value = "/tmp/test.pdf"

            result = project_service_mock.create_project(filename, file)

            assert result
            assert isinstance(result, Project)
            mock_upload.assert_called_once()
