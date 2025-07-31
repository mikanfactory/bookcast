from typing import BinaryIO

from bookcast.entities import Project


class ProjectService:
    @classmethod
    def fetch_all_projects(cls) -> list[Project]:
        pass

    @classmethod
    def find_project(cls, project_id: int) -> Project:
        pass

    @classmethod
    def create_project(cls, filename: str, file: BinaryIO) -> Project:
        pass
