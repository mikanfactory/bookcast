import asyncio
import json
import logging
import time
import traceback

from fastapi import APIRouter, Depends, HTTPException
from google.cloud import tasks_v2
from pydantic import BaseModel

from bookcast.config import (
    BOOKCAST_TTS_WORKER_QUEUE,
    BOOKCAST_WORKER_QUEUE,
    CLOUD_RUN_SERVICE_URL,
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_CLOUD_PROJECT,
)
from bookcast.dependencies import get_chapter_service, get_project_service
from bookcast.entities import ChapterStatus, ProjectStatus
from bookcast.services.audio_service import AudioService
from bookcast.services.chapter_service import ChapterService
from bookcast.services.ocr_service import OCRService
from bookcast.services.project_service import ProjectService
from bookcast.services.script_writing_service import ScriptWritingService
from bookcast.services.text_to_speach_service import TextToSpeechService

logger = logging.getLogger(__name__)

audio_service = AudioService()

router = APIRouter(
    prefix="/internal/api/v1/workers",
    tags=["workers"],
    responses={404: {"description": "Not found"}},
)


def success_response(message: str, data: dict) -> dict:
    response = {"success": True, "message": message}
    if data:
        response["data"] = data
    return response


class FormData(BaseModel):
    project_id: int


def invoke_task(project_id: int, fn_name: str, queue: str) -> dict:
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION, queue=queue)
    task_payload = {"project_id": project_id}
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{CLOUD_RUN_SERVICE_URL}/internal/api/v1/workers/{fn_name}",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(task_payload).encode(),
        },
        "dispatch_deadline": {"seconds": 60 * 60},  # 60 minutes
    }
    response = client.create_task(request={"parent": parent, "task": task})
    return {"task_name": response.name, "status": "queued"}


@router.post("/start_ocr")
async def start_ocr(
    data: FormData,
    project_service: ProjectService = Depends(get_project_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    ocr_service = OCRService(chapter_service)

    logger.info(f"Starting OCR for project ID: {data.project_id}...")

    project = project_service.find_project(data.project_id)
    chapters = chapter_service.select_chapter_by_project_id(data.project_id)
    if project.status != ProjectStatus.not_started:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"Project is not ready for OCR. Current status: {project.status.value}",
                "error_code": "INVALID_PROJECT_STATUS",
            },
        )

    logger.info(f"Updating project status to start OCR for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.start_ocr)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_ocr)

    start_time = time.time()
    await ocr_service.process(project, chapters)
    execution_time = time.time() - start_time

    logger.info(f"Updating project status to OCR completed for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.ocr_completed)

    try:
        logger.info("Invoking script writing worker...")
        task_result = invoke_task(data.project_id, "start_script_writing", BOOKCAST_WORKER_QUEUE)
    except Exception:
        logger.error(traceback.print_exc())
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": "Failed to invoke worker", "error_code": "WORKER_INVOCATION_FAILED"},
        )

    return success_response(
        message="OCR processing completed successfully",
        data={
            "project_id": data.project_id,
            "project_status": ProjectStatus.ocr_completed.value,
            "processed_chapters": len(chapters),
            "execution_time_seconds": round(execution_time, 2),
            "next_task": {
                "name": "start_script_writing",
                "task_id": task_result.get("task_name"),
            },
        },
    )


@router.post("/start_script_writing")
async def start_script_writing(
    data: FormData,
    project_service: ProjectService = Depends(get_project_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    script_writing_service = ScriptWritingService(chapter_service)

    logger.info(f"Starting script writing for project ID: {data.project_id}...")

    project = project_service.find_project(data.project_id)
    chapters = chapter_service.select_chapter_by_project_id(data.project_id)
    if project.status != ProjectStatus.ocr_completed:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"Project is not ready for script writing. Current status: {project.status.value}",
                "error_code": "INVALID_PROJECT_STATUS",
            },
        )

    logger.info(f"Updating project status to start writing script for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.start_writing_script)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_writing_script)

    start_time = time.time()
    await script_writing_service.process(project, chapters)
    execution_time = time.time() - start_time

    logger.info(f"Updating project status to script writing completed for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.writing_script_completed)

    try:
        logger.info("Invoking TTS worker...")
        task_result = invoke_task(data.project_id, "start_tts", BOOKCAST_TTS_WORKER_QUEUE)
    except Exception:
        logger.error(traceback.print_exc())
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": "Failed to invoke worker", "error_code": "WORKER_INVOCATION_FAILED"},
        )

    return success_response(
        message="Script writing completed successfully",
        data={
            "project_id": data.project_id,
            "project_status": ProjectStatus.writing_script_completed.value,
            "processed_chapters": len(chapters),
            "execution_time_seconds": round(execution_time, 2),
            "next_task": {"name": "start_tts", "task_id": task_result.get("task_name")},
        },
    )


@router.post("/start_tts")
async def start_tts(
    data: FormData,
    project_service: ProjectService = Depends(get_project_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    tts_service = TextToSpeechService(chapter_service)

    logger.info(f"Starting TTS for project ID: {data.project_id}...")

    project = project_service.find_project(data.project_id)
    chapters = chapter_service.select_chapter_by_project_id(data.project_id)
    if project.status != ProjectStatus.writing_script_completed:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"Project is not ready for TTS. Current status: {project.status.value}",
                "error_code": "INVALID_PROJECT_STATUS",
            },
        )

    logger.info(f"Updating project status to start TTS for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.start_tts)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_tts)

    start_time = time.time()
    await asyncio.wait_for(
        tts_service.generate_audio(project, chapters),
        timeout=60 * 60,  # 60 minutes timeout
    )
    execution_time = time.time() - start_time

    logger.info(f"Updating project status to TTS completed for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.tts_completed)

    try:
        logger.info("Invoking audio creation worker...")
        task_result = invoke_task(data.project_id, "start_creating_audio", BOOKCAST_WORKER_QUEUE)
    except Exception:
        logger.error(traceback.print_exc())
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": "Failed to invoke worker", "error_code": "WORKER_INVOCATION_FAILED"},
        )

    return success_response(
        message="TTS processing completed successfully",
        data={
            "project_id": data.project_id,
            "project_status": ProjectStatus.tts_completed.value,
            "processed_chapters": len(chapters),
            "execution_time_seconds": round(execution_time, 2),
            "next_task": {
                "name": "start_creating_audio",
                "task_id": task_result.get("task_name"),
            },
        },
    )


@router.post("/start_creating_audio")
async def start_creating_audio(
    data: FormData,
    project_service: ProjectService = Depends(get_project_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    project = project_service.find_project(data.project_id)
    chapters = chapter_service.select_chapter_by_project_id(data.project_id)
    if project.status != ProjectStatus.tts_completed:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": f"Project is not ready for audio creation. Current status: {project.status.value}",
                "error_code": "INVALID_PROJECT_STATUS",
            },
        )

    project_service.update_project_status(project, ProjectStatus.start_creating_audio)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_creating_audio)

    start_time = time.time()
    audio_service.generate_audio(project, chapters)
    execution_time = time.time() - start_time

    project_service.update_project_status(project, ProjectStatus.creating_audio_completed)
    chapter_service.update_chapters_status(chapters, ChapterStatus.creating_audio_completed)

    return success_response(
        message="Audio creation completed successfully",
        data={
            "project_id": data.project_id,
            "project_status": ProjectStatus.creating_audio_completed.value,
            "processed_chapters": len(chapters),
            "execution_time_seconds": round(execution_time, 2),
        },
    )
