import pytest

from bookcast.entities.project import Project, ProjectStatus
from bookcast.repositories.project_repository import ProjectRepository
from bookcast.services.db import supabase_client


class TestProjectRepository:
    @pytest.mark.integration
    def test_find(self):
        repo = ProjectRepository(supabase_client)
        project = repo.find(1)

        assert project.filename

        project = repo.find(100)
        assert project is None

    @pytest.mark.integration
    def test_create(self):
        repo = ProjectRepository(supabase_client)
        project = Project(filename="test_project", max_page_number=10)
        created_project = repo.create(project)

        assert created_project.id is not None
        assert created_project.created_at is not None
        assert created_project.updated_at is not None

    @pytest.mark.integration
    def test_update(self):
        repo = ProjectRepository(supabase_client)
        project = repo.find(1)

        project.status = ProjectStatus.start_ocr
        updated_project = repo.update(project)

        assert updated_project.id is not None
        assert updated_project.created_at is not None
        assert updated_project.updated_at is not None
