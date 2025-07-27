import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field


class Project(BaseModel):
    id: Optional[int] = Field(default=None, description="primary key")
    filename: str = Field(..., description="The name of the uploaded file")
    max_page_number: int = Field(..., description="The maximum page number of the uploaded file")
    created_at: Optional[dt.datetime] = Field(default=None, description="The timestamp when the project was created")
