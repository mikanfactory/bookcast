import datetime as dt
from enum import StrEnum

from pydantic import BaseModel, Field


class ProjectStatus(StrEnum):
    not_started = "not_started"
    progressing = "progressing"
    completed = "completed"


class Project(BaseModel):
    id: int | None = Field(default=None, description="primary key")
    filename: str = Field(..., description="The name of the uploaded file")
    max_page_number: int = Field(..., description="The maximum page number of the uploaded file")
    status: ProjectStatus = Field(default=ProjectStatus.not_started, description="The current status of the project")
    created_at: dt.datetime | None = Field(default=None, description="The timestamp when the project was created")
    updated_at: dt.datetime | None = Field(default=None, description="The timestamp when the project was last updated")
