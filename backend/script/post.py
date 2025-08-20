import requests
from functools import partial

from bookcast.config import CLOUD_RUN_SERVICE_URL
from bookcast.services.db import supabase_client
from bookcast.repositories import ChapterRepository, ProjectRepository
from bookcast.services.chapter import ChapterService
from bookcast.services.project import ProjectService


chapter_repository = ChapterRepository(supabase_client)
project_repository = ProjectRepository(supabase_client)

service_url = CLOUD_RUN_SERVICE_URL
# service_url = "http://localhost:8000"


def _post_project():
    url = f"{service_url}/api/v1/projects/upload_file"
    filename = "CPU入門"

    path = f"downloads/{filename}/{filename}.pdf"
    with open(path, "rb") as file:
        file_content = file.read()

    files = {"file": (filename + ".pdf", file_content, "application/pdf")}
    resp = requests.post(url, files=files)
    return resp


def _post_chapters(project_id, chapters):
    url = f"{service_url}/api/v1/chapters/create_chapters"

    json_value = {
        "project_id": project_id,
        "chapters": [
            {"chapter_number": chapter.chapter_number, "start_page": chapter.start_page, "end_page": chapter.end_page}
            for chapter in chapters
        ],
    }

    resp = requests.post(url, json=json_value)
    return resp


def post_project():
    project_service = ProjectService(project_repository, chapter_repository)
    chapter_service = ChapterService(chapter_repository, project_repository)

    result = _post_project()
    if result.ok:
        print(result.json())
        print("Project posted successfully.")
    else:
        print("Failed to post project.")
        print(result.text)


def post_chapters(project_id):
    chapter_service = ChapterService(chapter_repository, project_repository)
    chapters = chapter_service.select_chapter_by_project_id(13)

    result = _post_chapters(project_id, chapters)
    if result.ok:
        print(result.json())
        print("Project posted successfully.")
    else:
        print("Failed to post project.")
        print(result.text)


def _invoke(fn_name, project_id):
    url = f"{service_url}/internal/api/v1/workers/{fn_name}"
    json_value = {"project_id": project_id}
    resp = requests.post(url, json=json_value)
    if resp.ok:
        print(f"{fn_name} started successfully.")
    else:
        print(f"Failed to start {fn_name}.")
        print(resp.text)


invoke_ocr = partial(_invoke, "start_ocr")
invoke_script_writing = partial(_invoke, "start_script_writing")
invoke_tts = partial(_invoke, "start_tts")
invoke_create_audio = partial(_invoke, "start_creating_audio")


def main():
    project_id = 6
    # post_project()
    # post_chapters(project_id)
    # invoke_ocr(project_id)
    # invoke_script_writing(project_id)
    invoke_tts(project_id)
    # invoke_create_audio(project_id)


if __name__ == "__main__":
    main()
