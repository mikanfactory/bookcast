import io
import pathlib
import zipfile
from typing import BinaryIO, Generator

from bookcast.entities import Chapter, Project, ProjectStatus
from bookcast.repositories import ChapterRepository, ProjectRepository
from bookcast.services.file_service import CompletedAudioFileService, OCRImageFileService


def generate_zip(project: Project, chapters: list[Chapter]) -> Generator[bytes, None, None]:
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for chapter in chapters:
            path = CompletedAudioFileService.download_from_gcs(project.filename, chapter.chapter_number)
            zip_file.write(path, f"chapter_{chapter.chapter_number:03d}.wav")

    buffer.seek(0)
    while True:
        chunk = buffer.read(8192)
        if not chunk:
            break
        yield chunk


class ProjectService:
    def __init__(self, project_repo: ProjectRepository, chapter_repo: ChapterRepository):
        self.project_repo = project_repo
        self.chapter_repo = chapter_repo

    def fetch_all_projects(self) -> list[Project]:
        return self.project_repo.select_all()

    def find_project(self, project_id: int) -> Project | None:
        return self.project_repo.find(project_id)

    def create_project(self, filename: str, file: BinaryIO) -> Project | None:
        file_content = file.read()
        source_file_path = OCRImageFileService.write(filename, file_content)
        OCRImageFileService.upload_gcs_from_file(source_file_path)

        project = Project(filename=filename)
        return self.project_repo.create(project)

    def update_project_status(self, project: Project, status: ProjectStatus) -> Project:
        project.status = status
        self.project_repo.update(project)
        return project

    def create_download_archive(self, project_id: int) -> tuple[Generator[bytes, None, None], str]:
        project = self.project_repo.find(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")

        chapters = self.chapter_repo.select_chapter_by_project_id(project_id)
        filename = f"{pathlib.Path(project.filename).stem}.zip"
        return generate_zip(project, chapters), filename
