from pydantic import BaseModel


class ChapterStartPageNumber(BaseModel):
    page_number: int
    title: str


class ChapterViewModel(BaseModel):
    start_page: int = 0
    end_page: int = 0


class ProjectViewModel(BaseModel):
    project_id: int
    specified_max_chapter: int = 1
    chapters: dict[int, ChapterViewModel] = {}

    def validate_chapter_config(self):
        pass

        # Check for duplicate page numbers
        # specified_pages = set()
        # duplicates = []
        #
        # for chapter_num, config in self.chapters.items():
        #     if config.page_number in specified_pages:
        #         duplicates.append(config.page_number)
        #     else:
        #         specified_pages.add(config.page_number)
        #
        # if duplicates:
        #     error_msg = (
        #         f"ページ番号の重複があります。以下のページ番号が重複しています:\n\n{', '.join(map(str, duplicates))}"
        #     )
        #     raise Exception(error_msg)

    def add_chapter(self, chapter_num: int):
        config = ChapterViewModel(start_page_number=0, end_page_number=0)
        self.chapters[chapter_num] = config
        self.specified_max_chapter = max(self.specified_max_chapter, chapter_num)

    def set_chapter_start_page(self, chapter_num: int, start_page: int):
        if chapter_num not in self.chapters:
            self.add_chapter(chapter_num, start_page=start_page)
        else:
            self.chapters[chapter_num].start_page = start_page

    def set_chapter_end_page(self, chapter_num: int, end_page: int):
        if chapter_num not in self.chapters:
            self.add_chapter(chapter_num, end_page=end_page)
        else:
            self.chapters[chapter_num].end_page = end_page

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
            start_info = f"開始: P{config.start_page}" if config.start_page > 0 else "開始: 未設定"
            end_info = f"終了: P{config.end_page}" if config.end_page > 0 else "終了: 未設定"
            summary_lines.append(f"第{chapter_num}章: {start_info}, {end_info}")

        summary = "\n\n".join(summary_lines)
        return summary
