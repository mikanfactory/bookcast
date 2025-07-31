from fastapi import APIRouter, UploadFile

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def index():
    pass


@router.get("/{project_id}")
async def show(project_id: int):
    pass


@router.post("/upload_file")
async def upload_file(file: UploadFile):
    pass
