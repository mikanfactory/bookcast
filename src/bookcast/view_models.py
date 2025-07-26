from pydantic import BaseModel


class ChapterViewModel(BaseModel):
    page_number: int


class ChaptersViewModel(BaseModel):
    specified_max_chapter: int = 1
    chapters: dict[int, ChapterViewModel] = {}

    def validate_chapter_config(self):
        specified_max_chapter = self.specified_max_chapter

        # Check if all chapters up to max are configured
        if len(self.chapters) < specified_max_chapter:
            missing_chapters = []
            expected = range(1, specified_max_chapter + 1)
            actual = self.chapters.keys()

            for chapter_num in expected:
                if chapter_num not in actual:
                    missing_chapters.append(chapter_num)

            error_msg = (
                "章の設定が不完全です。すべての章を設定してください。\n\n"
                f"設定されていない章: {', '.join(map(str, missing_chapters))}"
            )
            raise Exception(error_msg)

        # Check for duplicate page numbers
        specified_pages = set()
        duplicates = []

        for chapter_num, config in self.chapters.items():
            if config.page_number in specified_pages:
                duplicates.append(config.page_number)
            else:
                specified_pages.add(config.page_number)

        if duplicates:
            error_msg = (
                f"ページ番号の重複があります。以下のページ番号が重複しています:\n\n{', '.join(map(str, duplicates))}"
            )
            raise Exception(error_msg)

    def add_chapter(self, chapter_num: int, page_number: int):
        config = ChapterViewModel(page_number=page_number)
        self.chapters[chapter_num] = config
        self.chapters.specified_max_chapter = max(self.chapters.specified_max_chapter, chapter_num)

    def get_chapter_summary(self) -> str:
        if not self.chapters:
            return "設定された章はありません。"

        summary_lines = []
        for chapter_num, config in sorted(self.chapters.items()):
            summary_lines.append(f"第{chapter_num}章: ページ {config.page_number}")

        summary = "\n\n".join(summary_lines)
        return summary
