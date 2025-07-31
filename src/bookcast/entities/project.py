import datetime as dt
from enum import StrEnum

from pydantic import BaseModel, Field


class ProjectStatus(StrEnum):
    not_started = "not_started"
    start_ocr = "start_ocr"
    ocr_completed = "ocr_completed"
    start_writing_script = "start_writing_script"
    writing_script_completed = "writing_script_completed"
    start_tts = "start_tts"
    tts_completed = "tts_completed"
    start_creating_audio = "start_creating_audio"
    creating_audio_completed = "creating_audio_completed"


class Project(BaseModel):
    id: int | None = Field(default=None, description="primary key")
    filename: str = Field(..., description="The name of the uploaded file")
    max_page_number: int = Field(..., description="The maximum page number of the uploaded file")
    status: ProjectStatus = Field(default=ProjectStatus.not_started, description="The current status of the project")
    created_at: dt.datetime | None = Field(default=None, description="The timestamp when the project was created")
    updated_at: dt.datetime | None = Field(default=None, description="The timestamp when the project was last updated")
