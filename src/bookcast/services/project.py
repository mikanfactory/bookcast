from typing import BinaryIO

from bookcast.entities import Project, ProjectStatus
from bookcast.repositories import ChapterRepository, ProjectRepository


class ProjectService:
    def __init__(self, project_repo: ProjectRepository, chapter_repo: ChapterRepository):
        self.project_repo = project_repo
        self.chapter_repo = chapter_repo

    def fetch_all_projects(self) -> list[Project]:
        return self.project_repo.select_all()

    def find_project(self, project_id: int) -> Project | None:
        return self.project_repo.find(project_id)

    def create_project(self, filename: str, file: BinaryIO) -> Project:
        pass

    def update_project_status(self, project: Project, status: ProjectStatus):
        project.status = status
        self.project_repo.update(project)
