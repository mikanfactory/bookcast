import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field


class Chapter(BaseModel):
    id: Optional[int] = Field(default=None, description="primary key")
    project_id: int = Field(..., description="The ID of the associated project")
    start_page: int = Field(..., description="The starting page number of the chapter")
    end_page: int = Field(..., description="The ending page number of the chapter")
    created_at: Optional[dt.datetime] = Field(default=None, description="The timestamp when the project was created")
