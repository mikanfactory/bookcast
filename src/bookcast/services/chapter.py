from bookcast.entities import Chapter, ChapterStatus, OCRWorkerResult, ScriptWritingWorkerResult
from bookcast.repositories import ChapterRepository, ProjectRepository
from bookcast.services.db import supabase_client

chapter_repository = ChapterRepository(supabase_client)
project_repository = ProjectRepository(supabase_client)


class ChapterService:
    @classmethod
    def select_chapters(cls, project_id: int) -> list[Chapter]:
        return chapter_repository.select_by_project_id(project_id)

    # TODO
    @classmethod
    def create_chapters(cls, project_id: int, chapters: list[Chapter]):
        pass

    @classmethod
    def update_chapters_status(cls, chapters: list[Chapter], status: ChapterStatus):
        for chapter in chapters:
            chapter.status = status
            chapter_repository.update(chapter)

    @classmethod
    def update_chapter_extracted_text(cls, chapters: list[Chapter], results: list[OCRWorkerResult]) -> None:
        results.sort(key=lambda x: x.page_number)

        for chapter in chapters:
            acc = []
            for result in results:
                if result.chapter_id == chapter.id:
                    acc.append(result.extracted_text)

            chapter.status = ChapterStatus.ocr_completed
            chapter.extracted_text = "\n".join(acc)
            chapter_repository.update(chapter)

    @classmethod
    def update_chapter_script(cls, chapters: list[Chapter], results: list[ScriptWritingWorkerResult]) -> None:
        for chapter in chapters:
            for result in results:
                if result.chapter_id == chapter.id:
                    chapter.script = result.script

            chapter.status = ChapterStatus.writing_script_completed
            chapter_repository.update(chapter)
