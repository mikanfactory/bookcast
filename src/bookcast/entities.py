from typing import List

from pydantic import BaseModel, Field

from bookcast.path_resolver import resolve_text_path


class Chapter(BaseModel):
    filename: str = Field(...)
    chapter_number: int = Field(...)
    start_page: int = Field(default=0, description="章の開始ページ番号")
    end_page: int = Field(default=0, description="章の終了ページ番号")
    extracted_texts: List[str] = Field(..., dscription="OCRで抽出されたテキストのリスト")
    script: str = Field(default="", description="章の台本")

    @property
    def source_text(self) -> str:
        acc = ""
        for t in self.extracted_texts:
            acc += t
            acc += "\n\n"

        return acc

    def __str__(self):
        return f"<Chapter {self.filename} - {self.chapter_number}章>"


def read_text_from_file(filename: str, page_number: int):
    file_path = resolve_text_path(filename, page_number + 1)
    with open(file_path, "r") as f:
        text = f.read()

    return text


def build_chapters(chapter_config: list[dict]) -> list[Chapter]:
    chapters = []
    for config in chapter_config:
        filename = config["filename"]
        start_page = config["start_page"]
        end_page = config["end_page"]
        chapter_number = config["chapter_number"]

        texts = []
        for i in range(start_page, end_page + 1):
            text = read_text_from_file(filename, i)
            texts.append(text)

        chapter = Chapter(
            filename=filename,
            chapter_number=chapter_number,
            start_page=start_page,
            end_page=end_page,
            extracted_texts=texts,
        )
        chapters.append(chapter)

    return chapters
