import pytest

from bookcast.entities.chapter import Chapter, ChapterStatus
from bookcast.repositories.chapter_repository import ChapterRepository
from bookcast.services.db import supabase_client


class TestChapterRepository:
    @pytest.mark.integration
    def test_find(self):
        repo = ChapterRepository(supabase_client)
        chapter = repo.find(14)
        assert chapter.project_id is not None

        chapter = repo.find(100)
        assert chapter is None

    @pytest.mark.integration
    def test_select_by_project_id(self):
        repo = ChapterRepository(supabase_client)
        chapters = repo.select_by_project_id(1)

        assert isinstance(chapters, list)
        assert isinstance(chapters[0], Chapter)

    @pytest.mark.integration
    def test_create(self):
        repo = ChapterRepository(supabase_client)
        chapter = Chapter(project_id=1, chapter_number=1, start_page=1, end_page=10)
        created_chapter = repo.create(chapter)

        assert created_chapter.id is not None
        assert created_chapter.created_at is not None
        assert created_chapter.updated_at is not None

    @pytest.mark.integration
    def test_update(self):
        repo = ChapterRepository(supabase_client)
        chapter = repo.find(30)

        chapter.status = ChapterStatus.start_ocr
        updated_chapter = repo.update(chapter)

        assert updated_chapter.id is not None
        assert updated_chapter.created_at is not None
        assert updated_chapter.updated_at is not None
