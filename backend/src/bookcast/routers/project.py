import traceback
from urllib.parse import quote
from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

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
    fname = quote(file.filename, safe='')
    logger.info(f"Received file upload: {fname}")
    try:
        results = project_service.create_project(fname, file.file)
    except Exception as e:
        logger.error(f"Error creating project from file {fname}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to create project from file")

    logger.info(f"Project created with ID: {results.id} for file: {fname}")
    if results:
        return results
    raise HTTPException(status_code=500, detail="Failed to create project from file")


@router.get("/{project_id}/download")
async def download_project(project_id: int, project_service: ProjectService = Depends(get_project_service)):
    logger.info(f"Creating download archive for project ID: {project_id}")
    try:
        zip_generator, filename = project_service.create_download_archive(project_id)
        return StreamingResponse(
            zip_generator,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename, safe='')}"},
        )
    except Exception as e:
        logger.error(f"Error creating download archive for project {project_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to create download archive")
