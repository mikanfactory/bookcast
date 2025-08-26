import pytest

from bookcast.entities.project import Project, ProjectStatus
from bookcast.repositories.project_repository import ProjectRepository


@pytest.fixture
def project_repository(supabase_client):
    return ProjectRepository(supabase_client)


class TestProjectRepository:
    @pytest.mark.integration
    def test_find(self, project_repository, completed_project):
        p, _ = completed_project
        project = project_repository.find(p.id)
        assert project.filename

        with pytest.raises(ValueError, match="Project id 999 not found"):
            project_repository.find(999)

    @pytest.mark.integration
    def test_create(self, project_repository):
        project = Project(filename="test_project")
        created_project = project_repository.create(project)

        assert created_project.id is not None
        assert created_project.created_at is not None
        assert created_project.updated_at is not None

    @pytest.mark.integration
    def test_update(self, project_repository, starting_project):
        p, _ = starting_project
        project = project_repository.find(p.id)

        project.status = ProjectStatus.start_ocr
        updated_project = project_repository.update(project)

        assert updated_project.id is not None
        assert updated_project.created_at is not None
        assert updated_project.updated_at is not None
