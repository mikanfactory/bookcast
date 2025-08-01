from fastapi import APIRouter

from bookcast.entities import ChapterStatus, ProjectStatus
from bookcast.services.audio import AudioService
from bookcast.services.chapter import ChapterService
from bookcast.services.file import TTSFileService
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

    ProjectService.update_project_status(project, ProjectStatus.start_ocr)
    ChapterService.update_chapters_status(chapters, ChapterStatus.start_ocr)

    results = ocr_service.process(project, chapters)

    ProjectService.update_project_status(project, ProjectStatus.ocr_completed)
    ChapterService.update_chapter_extracted_text(chapters, results)
    return {"status": 200}


@router.post("/start_script_writing/{project_id}")
async def start_script_writing(project_id: int):
    project = ProjectService.find_project(project_id)
    chapters = ChapterService.select_chapters(project_id)
    if project.status != ProjectStatus.ocr_completed:
        return {"status": 400}

    ProjectService.update_project_status(project, ProjectStatus.start_writing_script)
    ChapterService.update_chapters_status(chapters, ChapterStatus.start_writing_script)

    results = script_writing_service.process(project, chapters)

    ProjectService.update_project_status(project, ProjectStatus.writing_script_completed)
    ChapterService.update_chapter_script(chapters, results)
    return {"status": 200}


@router.post("/start_tts/{project_id}")
async def start_tts(project_id: int):
    project = ProjectService.find_project(project_id)
    chapters = ChapterService.select_chapters(project_id)
    if project.status != ProjectStatus.writing_script_completed:
        return {"status": 400}

    ProjectService.update_project_status(project, ProjectStatus.start_tts)
    ChapterService.update_chapters_status(chapters, ChapterStatus.start_tts)

    results = tts_service.generate_audio(project, chapters)

    ProjectService.update_project_status(project, ProjectStatus.tts_completed)
    ChapterService.update_chapter_script_file_count(chapters, results)
    return {"status": 200}


@router.post("/start_creating_audio/{project_id}")
async def start_creating_audio(project_id: int):
    project = ProjectService.find_project(project_id)
    chapters = ChapterService.select_chapters(project_id)
    if project.status != ProjectStatus.tts_completed:
        return {"status": 400}

    ProjectService.update_project_status(project, ProjectStatus.start_creating_audio)
    ChapterService.update_chapters_status(chapters, ChapterStatus.start_creating_audio)

    # TODO
    TTSFileService.download_from_gcs(project.filename, 1, 1)
    audio_service.generate_audio(project, chapters)

    ProjectService.update_project_status(project, ProjectStatus.creating_audio_completed)
    ChapterService.update_chapters_status(chapters, ChapterStatus.creating_audio_completed)
    return {"status": 200}
