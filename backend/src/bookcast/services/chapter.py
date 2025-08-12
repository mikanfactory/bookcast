from bookcast.entities import Chapter, ChapterStatus, OCRWorkerResult, ScriptWritingWorkerResult, TTSWorkerResult
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

    def update_chapters_status(self, chapters: list[Chapter], status: ChapterStatus) -> list[Chapter]:
        for chapter in chapters:
            chapter.status = status
            self.chapter_repo.update(chapter)

        return chapters

    def update_chapter_extracted_text(self, chapters: list[Chapter], results: list[OCRWorkerResult]) -> list[Chapter]:
        results.sort(key=lambda x: x.page_number)

        for chapter in chapters:
            acc = []
            for result in results:
                if result.chapter_id == chapter.id:
                    acc.append(result.extracted_text)

            chapter.status = ChapterStatus.ocr_completed
            chapter.extracted_text = "\n".join(acc)
            self.chapter_repo.update(chapter)

        return chapters

    def update_chapter_script(self, chapters: list[Chapter], results: list[ScriptWritingWorkerResult]) -> list[Chapter]:
        for chapter in chapters:
            for result in results:
                if result.chapter_id == chapter.id:
                    chapter.script = result.script

            chapter.status = ChapterStatus.writing_script_completed
            self.chapter_repo.update(chapter)

        return chapters

    def update_chapter_script_file_count(
        self, chapters: list[Chapter], results: list[TTSWorkerResult]
    ) -> list[Chapter]:
        results.sort(key=lambda x: x.index)

        for chapter in chapters:
            for result in results:
                if result.chapter_id == chapter.id:
                    chapter.script_file_count = result.index

            chapter.status = ChapterStatus.tts_completed
            self.chapter_repo.update(chapter)

        return chapters
