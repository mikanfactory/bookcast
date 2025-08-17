import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from bookcast.config import BOOKCAST_WORKER_QUEUE
from bookcast.dependencies import get_chapter_service
from bookcast.entities.chapter import Chapter
from bookcast.internal.worker import invoke_task
from bookcast.services.chapter import ChapterService

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
    try:
        result = chapter_service.create_chapters(chapters)
        if len(result) > 0:
            logger.info(f"Chapters created successfully for project {project.project_id}")
            return {"message": "Chapters created successfully", "chapters": result}
    except Exception as e:
        logger.error(f"Error creating chapters for project {project.project_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to create chapters for project")

    try:
        logger.info("Invoking OCR worker for project %s", project.project_id)
        invoke_task(project.project_id, "start_ocr", BOOKCAST_WORKER_QUEUE)
    except Exception as e:
        logger.error(traceback.print_exc())
        raise HTTPException(500, detail=f"Failed to invoke worker: {str(e)}")
