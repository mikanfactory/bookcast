import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field

from bookcast.path_resolver import resolve_text_path


class Chapter(BaseModel):
    id: Optional[int] = Field(default=None, description="primary key")
    project_id: int = Field(..., description="The ID of the associated project")
    chapter_number: int = Field(..., description="The chapter number in the project")
    start_page: int = Field(..., description="The starting page number of the chapter")
    end_page: int = Field(..., description="The ending page number of the chapter")
    extracted_text: Optional[str] = Field(default=None, description="The extracted text from the chapter")
    created_at: Optional[dt.datetime] = Field(default=None, description="The timestamp when the project was created")

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
