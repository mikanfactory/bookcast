import pytest

from bookcast.entities.chapter import Chapter, ChapterStatus
from bookcast.repositories.chapter_repository import ChapterRepository


@pytest.fixture
def chapter_repository(supabase_client):
    return ChapterRepository(supabase_client)


class TestChapterRepository:
    @pytest.mark.integration
    def test_find(self, chapter_repository, completed_project):
        _, cs = completed_project
        chapter = chapter_repository.find(cs[0].id)
        assert chapter.project_id is not None

        with pytest.raises(ValueError, match="Chapter id 100 not found"):
            chapter_repository.find(100)

    @pytest.mark.integration
    def test_select_by_project_id(self, chapter_repository, completed_project):
        p, _ = completed_project
        chapters = chapter_repository.select_chapter_by_project_id(p.id)

        assert isinstance(chapters, list)
        assert isinstance(chapters[0], Chapter)

    @pytest.mark.integration
    def test_create(self, chapter_repository, starting_project):
        p, _ = starting_project
        chapter = Chapter(project_id=p.id, chapter_number=2, start_page=1, end_page=10)
        created_chapter = chapter_repository.create(chapter)

        assert created_chapter.id is not None
        assert created_chapter.created_at is not None
        assert created_chapter.updated_at is not None

    @pytest.mark.integration
    def test_bulk_create(self, chapter_repository, starting_project):
        p, _ = starting_project
        chapters = [Chapter(project_id=p.id, chapter_number=2, start_page=1, end_page=10)]
        created_chapter = chapter_repository.bulk_create(chapters)

        assert created_chapter[0].id is not None
        assert created_chapter[0].created_at is not None
        assert created_chapter[0].updated_at is not None

    @pytest.mark.integration
    def test_update(self, chapter_repository, starting_project):
        _, cs = starting_project
        chapter = chapter_repository.find(cs[0].id)

        chapter.status = ChapterStatus.start_ocr
        updated_chapter = chapter_repository.update(chapter)

        assert updated_chapter.id is not None
        assert updated_chapter.created_at is not None
        assert updated_chapter.updated_at is not None
