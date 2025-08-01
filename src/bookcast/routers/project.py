from fastapi import APIRouter, UploadFile

from bookcast.entities import Project
from bookcast.services.project import ProjectService

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def index() -> list[Project]:
    return ProjectService.fetch_all_projects()


@router.get("/{project_id}")
async def show(project_id: int) -> Project:
    return ProjectService.find_project(project_id)


@router.post("/upload_file")
async def upload_file(file: UploadFile):
    return ProjectService.create_project(file.filename, file.file)
