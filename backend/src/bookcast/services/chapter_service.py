from bookcast.entities import Chapter, ChapterStatus
from bookcast.repositories import ChapterRepository, ProjectRepository


class ChapterService:
    def __init__(self, chapter_repo: ChapterRepository, project_repo: ProjectRepository):
        self.chapter_repo = chapter_repo
        self.project_repo = project_repo

    def select_chapter_by_project_id(self, project_id: int) -> list[Chapter]:
        return self.chapter_repo.select_chapter_by_project_id(project_id)

    def create_chapters(self, chapters: list[Chapter]):
        self.chapter_repo.bulk_create(chapters)
        return chapters

    def update(self, chapter: Chapter) -> Chapter:
        self.chapter_repo.update(chapter)
        return chapter

    def update_chapters_status(self, chapters: list[Chapter], status: ChapterStatus) -> list[Chapter]:
        for chapter in chapters:
            chapter.status = status
            self.chapter_repo.update(chapter)

        return chapters

    def update_chapters_status_by_condition(self, chapters: list[Chapter], before: ChapterStatus, after: ChapterStatus) -> list[Chapter]:
        for chapter in chapters:
            if chapter.status == before:
                chapter.status = after
                self.chapter_repo.update(chapter)

        return chapters
