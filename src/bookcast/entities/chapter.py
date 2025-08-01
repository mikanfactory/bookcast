import datetime as dt
from enum import StrEnum

from pydantic import BaseModel, Field


class ChapterStatus(StrEnum):
    not_started = "not_started"
    start_ocr = "start_ocr"
    ocr_completed = "ocr_completed"
    start_writing_script = "start_writing_script"
    writing_script_completed = "writing_script_completed"
    start_tts = "start_tts"
    tts_completed = "tts_completed"
    start_creating_audio = "start_creating_audio"
    creating_audio_completed = "creating_audio_completed"


class Chapter(BaseModel):
    id: int | None = Field(default=None, description="primary key")
    project_id: int = Field(..., description="The ID of the associated project")
    chapter_number: int = Field(..., description="The chapter number in the project")
    start_page: int = Field(..., description="The starting page number of the chapter")
    end_page: int = Field(..., description="The ending page number of the chapter")
    extracted_text: str = Field(default="", description="The extracted text from the chapter")
    script: str = Field(default="", description="The script generated from extracted_text")
    status: ChapterStatus = Field(default=ChapterStatus.not_started, description="The current status of the chapter")
    created_at: dt.datetime | None = Field(default=None, description="The timestamp when the project was created")
    updated_at: dt.datetime | None = Field(default=None, description="The timestamp when the project was last updated")
