import traceback
from logging import getLogger
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from bookcast.dependencies import get_project_service
from bookcast.entities import Project
from bookcast.services.project_service import ProjectService

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
    if not results:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Project not found",
                "error_code": "PROJECT_NOT_FOUND",
            },
        )

    return results


@router.post("/upload_file")
async def upload_file(file: UploadFile, project_service: ProjectService = Depends(get_project_service)):
    fname = quote(file.filename, safe="")
    logger.info(f"Received file upload: {fname}")
    try:
        results = project_service.create_project(fname, file.file)
    except RuntimeError as e:
        logger.error(f"Runtime error creating project from file {fname}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": str(e),
                "error_code": "PROJECT_CREATION_FAILED",
            },
        )

    logger.info(f"Project created with ID: {results.id} for file: {fname}")
    return results


@router.get("/{project_id}/download")
async def download_project(project_id: int, project_service: ProjectService = Depends(get_project_service)):
    logger.info(f"Creating download archive for project ID: {project_id}")

    try:
        project = project_service.find_project(project_id)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Project not found",
                "error_code": "PROJECT_NOT_FOUND",
            },
        )

    zip_generator, filename = project_service.create_download_archive(project)
    return StreamingResponse(
        zip_generator,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename, safe='')}"},
    )
