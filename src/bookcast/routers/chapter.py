from fastapi import APIRouter, Depends, Form
from pydantic import BaseModel

from bookcast.dependencies import get_chapter_service
from bookcast.services.chapter import ChapterService


class FormData(BaseModel):
    pass


router = APIRouter(
    prefix="/api/v1/chapters",
    tags=["chapters"],
    responses={404: {"description": "Not found"}},
)


@router.post("/create_chapters")
async def create_chapters(
    data: FormData = Form(),
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    pass
