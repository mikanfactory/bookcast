from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from bookcast.dependencies import get_project_service
from bookcast.entities import Project
from bookcast.services.project import ProjectService

logger = getLogger(__name__)

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
    if results:
        return results
    raise HTTPException(status_code=404, detail="Project not found")


@router.post("/upload_file")
async def upload_file(file: UploadFile, project_service: ProjectService = Depends(get_project_service)):
    logger.info(f"Received file upload: {file.filename}")
    try:
        results = project_service.create_project(file.filename, file.file)
    except Exception as e:
        logger.error(f"Error creating project from file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project from file")

    logger.info(f"Project created with ID: {results.id} for file: {file.filename}")
    if results:
        return results
    raise HTTPException(status_code=500, detail="Failed to create project from file")
