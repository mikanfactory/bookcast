from fastapi import APIRouter, Depends

from bookcast.dependencies import get_chapter_service, get_project_service
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
async def start_ocr(
    project_id: int,
    project_service: ProjectService = Depends(get_project_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    project = project_service.find_project(project_id)
    chapters = chapter_service.select_chapter_by_project_id(project_id)
    if project.status != ProjectStatus.not_started:
        return {"status": 400}

    project_service.update_project_status(project, ProjectStatus.start_ocr)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_ocr)

    results = ocr_service.process(project, chapters)

    project_service.update_project_status(project, ProjectStatus.ocr_completed)
    chapter_service.update_chapter_extracted_text(chapters, results)
    return {"status": 200}


@router.post("/start_script_writing/{project_id}")
async def start_script_writing(
    project_id: int,
    project_service: ProjectService = Depends(get_project_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    project = project_service.find_project(project_id)
    chapters = chapter_service.select_chapter_by_project_id(project_id)
    if project.status != ProjectStatus.ocr_completed:
        return {"status": 400}

    project_service.update_project_status(project, ProjectStatus.start_writing_script)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_writing_script)

    results = script_writing_service.process(project, chapters)

    project_service.update_project_status(project, ProjectStatus.writing_script_completed)
    chapter_service.update_chapter_script(chapters, results)
    return {"status": 200}


@router.post("/start_tts/{project_id}")
async def start_tts(
    project_id: int,
    project_service: ProjectService = Depends(get_project_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    project = project_service.find_project(project_id)
    chapters = chapter_service.select_chapter_by_project_id(project_id)
    if project.status != ProjectStatus.writing_script_completed:
        return {"status": 400}

    project_service.update_project_status(project, ProjectStatus.start_tts)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_tts)

    results = tts_service.generate_audio(project, chapters)

    project_service.update_project_status(project, ProjectStatus.tts_completed)
    chapter_service.update_chapter_script_file_count(chapters, results)
    return {"status": 200}


@router.post("/start_creating_audio/{project_id}")
async def start_creating_audio(
    project_id: int,
    project_service: ProjectService = Depends(get_project_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
):
    project = project_service.find_project(project_id)
    chapters = chapter_service.select_chapter_by_project_id(project_id)
    if project.status != ProjectStatus.tts_completed:
        return {"status": 400}

    project_service.update_project_status(project, ProjectStatus.start_creating_audio)
    chapter_service.update_chapters_status(chapters, ChapterStatus.start_creating_audio)

    for chapter in chapters:
        for i in range(chapter.script_file_count):
            TTSFileService.download_from_gcs(project.filename, chapter.id, i)

    audio_service.generate_audio(project, chapters)

    project_service.update_project_status(project, ProjectStatus.creating_audio_completed)
    chapter_service.update_chapters_status(chapters, ChapterStatus.creating_audio_completed)
    return {"status": 200}
