from fastapi import APIRouter, Depends, HTTPException, UploadFile

from bookcast.dependencies import get_project_service
from bookcast.entities import Project
from bookcast.services.project import ProjectService

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def index(project_service: ProjectService = Depends(get_project_service)) -> list[Project]:
    return project_service.fetch_all_projects()


@router.get("/{project_id}")
async def show(project_id: int, project_service: ProjectService = Depends(get_project_service)) -> Project:
    results = project_service.find_project(project_id)
    print(results)
    if results:
        return results
    raise HTTPException(status_code=404, detail="Project not found")


@router.post("/upload_file")
async def upload_file(file: UploadFile, project_service: ProjectService = Depends(get_project_service)):
    return project_service.create_project(file.filename, file.file)
