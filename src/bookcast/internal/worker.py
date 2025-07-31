from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1/workers",
    tags=["workers"],
    responses={404: {"description": "Not found"}},
)


@router.post("/start_ocr/{project_id}")
async def start_ocr(project_id: int):
    pass


@router.post("/start_script_writing/{project_id}")
async def start_script_writing(project_id: int):
    pass


@router.post("/start_tts/{project_id}")
async def start_tts(project_id: int):
    pass


@router.post("/start_creating_audio/{project_id}")
async def start_creating_audio(project_id: int):
    pass
