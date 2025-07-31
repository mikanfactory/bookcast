from fastapi import FastAPI

from bookcast.internal import worker
from bookcast.routers import chapter, project

app = FastAPI()

app.include_router(project.router)
app.include_router(chapter.router)
app.include_router(worker.router, prefix="/internal")
