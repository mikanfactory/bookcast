import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from bookcast.config import BOOKCAST_WORKER_QUEUE
from bookcast.dependencies import get_chapter_service
from bookcast.entities.chapter import Chapter
from bookcast.internal.worker import invoke_task
from bookcast.services.chapter_service import ChapterService

logger = logging.getLogger(__name__)


class ChapterForm(BaseModel):
    chapter_number: int
    start_page: int
    end_page: int


class ProjectForm(BaseModel):
    project_id: int
    chapters: list[ChapterForm]


router = APIRouter(
    prefix="/api/v1/chapters",
    tags=["chapters"],
    responses={404: {"description": "Not found"}},
)


@router.post("/create_chapters")
async def create_chapters(
    project: ProjectForm,
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    chapters = [
        Chapter(
            project_id=project.project_id,
            chapter_number=chapter.chapter_number,
            start_page=chapter.start_page,
            end_page=chapter.end_page,
        )
        for chapter in project.chapters
    ]
    result = chapter_service.create_chapters(chapters)
    if len(result) == 0:
        logger.warning(f"No chapters were created for project {project.project_id}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "No chapters were created",
                "error_code": "NO_CHAPTERS_CREATED",
            },
        )

    logger.info(f"Chapters created successfully for project {project.project_id}")
    logger.info(f"Invoking OCR worker for project {project.project_id}")
    result = invoke_task(project.project_id, "start_ocr", BOOKCAST_WORKER_QUEUE)

    return {"success": True, "message": "Chapters created and OCR worker invoked", "data": result}
