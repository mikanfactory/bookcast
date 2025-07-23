from typing import Optional

from pydantic import BaseModel


class ChapterConfig(BaseModel):
    page_number: int


class Chapters(BaseModel):
    specified_max_chapter: int = 1
    chapters: dict[int, ChapterConfig] = {}


class PodcastSetting(BaseModel):
    num_of_people: int
    personality1_name: str
    personality2_name: str
    length: int
    prompt: Optional[str]
