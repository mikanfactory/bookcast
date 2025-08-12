import logging
from fastapi import APIRouter, Depends, Form
from pydantic import BaseModel

from bookcast.dependencies import get_chapter_service
from bookcast.services.chapter import ChapterService

logger = logging.getLogger(__name__)


class Chapter(BaseModel):
    chapter_number: int
    start_page: int
    end_page: int


class Project(BaseModel):
    project_id: int
    chapters: list[Chapter]


router = APIRouter(
    prefix="/api/v1/chapters",
    tags=["chapters"],
    responses={404: {"description": "Not found"}},
)


@router.post("/create_chapters")
async def create_chapters(
    project: Project,
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    logger.info(project)
    pass
