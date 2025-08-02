from typing import BinaryIO

from bookcast.entities import Project, ProjectStatus
from bookcast.repositories import ChapterRepository, ProjectRepository
from bookcast.services.db import supabase_client

chapter_repository = ChapterRepository(supabase_client)
project_repository = ProjectRepository(supabase_client)


class ProjectService:
    @classmethod
    def fetch_all_projects(cls) -> list[Project]:
        return project_repository.select_all()

    @classmethod
    def find_project(cls, project_id: int) -> Project:
        return project_repository.find(project_id)

    @classmethod
    def create_project(cls, filename: str, file: BinaryIO) -> Project:
        pass

    @classmethod
    def update_project_status(cls, project: Project, status: ProjectStatus):
        project.status = status
        project_repository.update(project)
