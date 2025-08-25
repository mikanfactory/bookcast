import pathlib
import tempfile
import zipfile
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from bookcast.entities import Chapter, ChapterStatus, Project, ProjectStatus
from bookcast.services import file_service
from bookcast.services.project_service import ProjectService


def create_mock_project_service():
    mock_project_repo = MagicMock()
    mock_chapter_repo = MagicMock()
    return ProjectService(mock_project_repo, mock_chapter_repo)


@pytest.fixture
def project_service_mock():
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
        project = Project(id=1, filename="test.pdf", status=ProjectStatus.not_started)
        new_status = ProjectStatus.start_ocr

        project_service_mock.update_project_status(project, new_status)

        assert project.status == new_status
        project_service_mock.project_repo.update.assert_called_once_with(project)


class TestCreateProject:
    @patch.object(file_service.OCRImageFileService, "write", return_value="/tmp/test.pdf")
    @patch.object(file_service.OCRImageFileService, "upload_gcs_from_file")
    def test_create_project(self, mock_upload, mock_write, project_service_mock):
        filename = "test.pdf"
        file_content = b"mock file content"
        file = BytesIO(file_content)

        result = project_service_mock.create_project(filename, file)

        assert result
        assert isinstance(result, Project)
        mock_upload.assert_called_once()


class TestCreateDownloadArchive:
    @patch.object(file_service.CompletedAudioFileService, "download_from_gcs")
    def test_create_download_archive_success(self, mock_download, project_service_mock):
        project_id = 1
        project = Project(id=1, filename="test.pdf", status=ProjectStatus.creating_audio_completed)
        chapters = [
            Chapter(
                id=1,
                project_id=1,
                chapter_number=1,
                start_page=1,
                end_page=10,
                status=ChapterStatus.creating_audio_completed,
            ),
            Chapter(
                id=2,
                project_id=1,
                chapter_number=2,
                start_page=11,
                end_page=20,
                status=ChapterStatus.creating_audio_completed,
            ),
        ]

        project_service_mock.project_repo.find.return_value = project
        project_service_mock.chapter_repo.select_chapter_by_project_id.return_value = chapters

        with tempfile.TemporaryDirectory() as temp_dir:
            chapter1_path = pathlib.Path(temp_dir) / "chapter1.wav"
            chapter2_path = pathlib.Path(temp_dir) / "chapter2.wav"

            chapter1_path.write_bytes(b"dummy audio data 1")
            chapter2_path.write_bytes(b"dummy audio data 2")

            mock_download.side_effect = [str(chapter1_path), str(chapter2_path)]

            zip_generator, filename = project_service_mock.create_download_archive(project_id)

            assert filename == "test.zip"
            assert zip_generator is not None

            zip_data = b"".join(zip_generator)

            assert len(zip_data) > 0

            with zipfile.ZipFile(BytesIO(zip_data), "r") as zip_file:
                file_list = zip_file.namelist()
                assert len(file_list) == 2
                assert "chapter_001.wav" in file_list
                assert "chapter_002.wav" in file_list

                assert zip_file.read("chapter_001.wav") == b"dummy audio data 1"
                assert zip_file.read("chapter_002.wav") == b"dummy audio data 2"

            project_service_mock.project_repo.find.assert_called_once_with(project_id)
            project_service_mock.chapter_repo.select_chapter_by_project_id.assert_called_once_with(project_id)
