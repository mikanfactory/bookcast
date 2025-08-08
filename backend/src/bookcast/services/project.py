from typing import BinaryIO

from pdf2image import convert_from_path

from bookcast.entities import Project, ProjectStatus
from bookcast.repositories import ChapterRepository, ProjectRepository
from bookcast.services.file import OCRImageFileService


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

        images = convert_from_path(source_file_path)
        project = Project(filename=filename, max_page_number=len(images))
        return self.project_repo.create(project)

    def update_project_status(self, project: Project, status: ProjectStatus) -> Project:
        project.status = status
        self.project_repo.update(project)
        return project
