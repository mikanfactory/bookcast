from fastapi import APIRouter

from bookcast.entities import ProjectStatus
from bookcast.services.audio import AudioService
from bookcast.services.chapter import ChapterService
from bookcast.services.ocr import OCRService
from bookcast.services.project import ProjectService
from bookcast.services.script_writing import ScriptWritingService
from bookcast.services.tts import TextToSpeechService

ocr_service = OCRService()
script_writing_service = ScriptWritingService()
tts_service = TextToSpeechService()
audio_service = AudioService()

router = APIRouter(
    prefix="/api/v1/workers",
    tags=["workers"],
    responses={404: {"description": "Not found"}},
)


@router.post("/start_ocr/{project_id}")
async def start_ocr(project_id: int):
    project = ProjectService.find_project(project_id)
    chapters = ChapterService.select_chapters(project_id)
    if project.status != ProjectStatus.not_started:
        return {"status": 400}

    ocr_service.process(project, chapters)
    return {"status": 200}


@router.post("/start_script_writing/{project_id}")
async def start_script_writing(project_id: int):
    project = ProjectService.find_project(project_id)
    chapters = ChapterService.select_chapters(project_id)
    if project.status != ProjectStatus.ocr_completed:
        return {"status": 400}

    script_writing_service.process(project, chapters)

    return {"status": 200}


@router.post("/start_tts/{project_id}")
async def start_tts(project_id: int):
    project = ProjectService.find_project(project_id)
    chapters = ChapterService.select_chapters(project_id)
    if project.status != ProjectStatus.writing_script_completed:
        return {"status": 400}

    tts_service.generate_audio(project, chapters)
    return {"status": 200}


@router.post("/start_creating_audio/{project_id}")
async def start_creating_audio(project_id: int):
    project = ProjectService.find_project(project_id)
    chapters = ChapterService.select_chapters(project_id)
    if project.status != ProjectStatus.tts_completed:
        return {"status": 400}

    audio_service.generate_audio(project, chapters)
    return {"status": 200}
