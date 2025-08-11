from pydantic import BaseModel


class ChapterViewModel(BaseModel):
    start_page_number: int = 0
    end_page_number: int = 0
    page_number: int


class ProjectViewModel(BaseModel):
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

    def add_chapter(self, chapter_num: int, start_page: int = None, end_page: int = None):
        # Keep backward compatibility with page_number
        page_number = start_page or 0
        config = ChapterViewModel(
            page_number=page_number, start_page_number=start_page or 0, end_page_number=end_page or 0
        )
        self.chapters[chapter_num] = config
        self.specified_max_chapter = max(self.specified_max_chapter, chapter_num)

    def set_chapter_start_page(self, chapter_num: int, start_page: int):
        if chapter_num not in self.chapters:
            self.add_chapter(chapter_num, start_page=start_page)
        else:
            self.chapters[chapter_num].start_page_number = start_page
            self.chapters[chapter_num].page_number = start_page  # For backward compatibility

    def set_chapter_end_page(self, chapter_num: int, end_page: int):
        if chapter_num not in self.chapters:
            self.add_chapter(chapter_num, end_page=end_page)
        else:
            self.chapters[chapter_num].end_page_number = end_page

    def remove_chapter(self, chapter_num: int):
        if chapter_num in self.chapters:
            del self.chapters[chapter_num]

    def get_chapter_info(self, chapter_num: int) -> ChapterViewModel:
        return self.chapters.get(chapter_num, ChapterViewModel(page_number=0))

    def get_chapter_summary(self) -> str:
        if not self.chapters:
            return "設定された章はありません。"

        summary_lines = []
        for chapter_num, config in sorted(self.chapters.items()):
            start_info = f"開始: P{config.start_page_number}" if config.start_page_number > 0 else "開始: 未設定"
            end_info = f"終了: P{config.end_page_number}" if config.end_page_number > 0 else "終了: 未設定"
            summary_lines.append(f"第{chapter_num}章: {start_info}, {end_info}")

        summary = "\n\n".join(summary_lines)
        return summary
