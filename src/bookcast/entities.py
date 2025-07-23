from typing import List
from pydantic import BaseModel, Field


class Chapter(BaseModel):
    filename: str = Field(...)
    chapter_number: int = Field(...)
    extracted_texts: List[str] = Field(...)

    @property
    def source_text(self) -> str:
        acc = ""
        for t in self.extracted_texts:
            acc += t
            acc += "\n\n"

        return acc


