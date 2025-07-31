from typing import Annotated

from fastapi import APIRouter, Form
from pydantic import BaseModel


class FormData(BaseModel):
    pass


router = APIRouter(
    prefix="/api/v1/chapters",
    tags=["chapters"],
    responses={404: {"description": "Not found"}},
)


@router.post("/create_chapters")
async def create_chapters(data: Annotated[FormData, Form()]):
    pass
