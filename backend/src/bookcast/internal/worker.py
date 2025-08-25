import asyncio
import json
import logging
import traceback
from typing import Optional

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


class FormData(BaseModel):
    project_id: int


def invoke_task(project_id: int, fn_name: str, queue: str) -> Optional[dict]:
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
    # if project.status != ProjectStatus.not_started:
    #     return {"status": 400}

    logger.info(f"Updating project status to start OCR for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.start_ocr)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_ocr)

    await ocr_service.process(project, chapters)

    logger.info(f"Updating project status to OCR completed for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.ocr_completed)

    try:
        logger.info("Invoking script writing worker...")
        invoke_task(data.project_id, "start_script_writing", BOOKCAST_WORKER_QUEUE)
    except Exception as e:
        logger.error(traceback.print_exc())
        raise HTTPException(500, detail=f"Failed to invoke worker: {str(e)}")

    return {"status": 200}


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
    # if project.status != ProjectStatus.ocr_completed:
    #     return {"status": 400}

    logger.info(f"Updating project status to start writing script for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.start_writing_script)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_writing_script)

    await script_writing_service.process(project, chapters)

    logger.info(f"Updating project status to script writing completed for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.writing_script_completed)

    try:
        logger.info("Invoking TTS worker...")
        invoke_task(data.project_id, "start_tts", BOOKCAST_TTS_WORKER_QUEUE)
    except Exception as e:
        logger.error(traceback.print_exc())
        raise HTTPException(500, detail=f"Failed to invoke worker: {str(e)}")

    return {"status": 200}


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
    # if project.status != ProjectStatus.writing_script_completed:
    #     return {"status": 400}

    logger.info(f"Updating project status to start TTS for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.start_tts)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_tts)

    await asyncio.wait_for(
        tts_service.generate_audio(project, chapters),
        timeout=60 * 60,  # 60 minutes timeout
    )

    logger.info(f"Updating project status to TTS completed for project ID: {data.project_id}...")
    project_service.update_project_status(project, ProjectStatus.tts_completed)

    try:
        logger.info("Invoking audio creation worker...")
        invoke_task(data.project_id, "start_creating_audio", BOOKCAST_WORKER_QUEUE)
    except Exception as e:
        logger.error(traceback.print_exc())
        raise HTTPException(500, detail=f"Failed to invoke worker: {str(e)}")

    return {"status": 200}


@router.post("/start_creating_audio")
async def start_creating_audio(
    data: FormData,
    project_service: ProjectService = Depends(get_project_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    project = project_service.find_project(data.project_id)
    chapters = chapter_service.select_chapter_by_project_id(data.project_id)
    # if project.status != ProjectStatus.tts_completed:
    #     return {"status": 400}

    project_service.update_project_status(project, ProjectStatus.start_creating_audio)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_creating_audio)

    audio_service.generate_audio(project, chapters)

    project_service.update_project_status(project, ProjectStatus.creating_audio_completed)
    chapter_service.update_chapters_status(chapters, ChapterStatus.creating_audio_completed)
    return {"status": 200}
