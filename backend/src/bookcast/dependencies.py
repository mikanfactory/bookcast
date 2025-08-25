from bookcast.repositories import ChapterRepository, ProjectRepository
from bookcast.services.chapter_service import ChapterService
from bookcast.services.db import supabase_client
from bookcast.services.project_service import ProjectService


def get_project_service() -> ProjectService:
    chapter_repo = ChapterRepository(supabase_client)
    project_repo = ProjectRepository(supabase_client)
    return ProjectService(project_repo, chapter_repo)


def get_chapter_service() -> ChapterService:
    chapter_repo = ChapterRepository(supabase_client)
    project_repo = ProjectRepository(supabase_client)
    return ChapterService(chapter_repo, project_repo)
