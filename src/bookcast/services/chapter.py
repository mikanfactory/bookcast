from bookcast.entities import Chapter, ChapterStatus
from bookcast.repositories import ChapterRepository, ProjectRepository
from bookcast.services.db import supabase_client

chapter_repository = ChapterRepository(supabase_client)
project_repository = ProjectRepository(supabase_client)


class ChapterService:
    @classmethod
    def select_chapters(cls, project_id: int) -> list[Chapter]:
        pass

    # TODO
    @classmethod
    def create_chapters(cls, project_id: int, chapters: list[Chapter]):
        pass

    @classmethod
    def update_chapters_status(cls, chapters: list[Chapter], status: ChapterStatus):
        for chapter in chapters:
            chapter.status = status
            chapter_repository.update(chapter)
