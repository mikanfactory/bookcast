import pytest

from bookcast.config import SUPABASE_API_KEY, SUPABASE_PROJECT_URL
from bookcast.entities import Chapter, Project
from supabase import create_client


@pytest.fixture(scope="session")
def supabase_client():
    return create_client(SUPABASE_PROJECT_URL, SUPABASE_API_KEY)


@pytest.fixture(scope="session", autouse=True)
def cleanup_tables(supabase_client):
    yield
    tables = ["chapter", "project"]
    for t in tables:
        supabase_client.table(t).delete().neq("id", 0).execute()


@pytest.fixture(scope="session")
def completed_project(supabase_client):
    project_result = (
        supabase_client.table("project")
        .insert(
            [
                {
                    "filename": "test1.pdf",
                    "max_page_number": 2,
                    "status": "creating_audio_completed",
                },
            ]
        )
        .execute()
    )
    projects = [Project(**data) for data in project_result.data]

    chapter_result = (
        supabase_client.table("chapter")
        .insert(
            [
                {
                    "project_id": projects[0].id,
                    "chapter_number": 1,
                    "start_page": 1,
                    "end_page": 2,
                    "status": "creating_audio_completed",
                    "script": "Speaker1: Hello there.\nSpeaker2: Hello back.",
                    "script_file_count": 1,
                },
                {
                    "project_id": projects[0].id,
                    "chapter_number": 2,
                    "start_page": 3,
                    "end_page": 3,
                    "status": "creating_audio_completed",
                    "script": "Speaker1: Goodbye now.\nSpeaker2: See you tomorrow.",
                    "script_file_count": 1,
                },
            ]
        )
        .execute()
    )
    chapters = [Chapter(**data) for data in chapter_result.data]
    yield projects[0], chapters


@pytest.fixture(scope="session")
def starting_project(supabase_client):
    project_result = (
        supabase_client.table("project")
        .insert(
            [
                {
                    "filename": "test2.pdf",
                    "max_page_number": 3,
                    "status": "not_started",
                },
            ]
        )
        .execute()
    )
    projects = [Project(**data) for data in project_result.data]

    chapter_result = (
        supabase_client.table("chapter")
        .insert(
            [
                {
                    "project_id": projects[0].id,
                    "chapter_number": 1,
                    "start_page": 1,
                    "end_page": 2,
                    "status": "not_started",
                    "script": "",
                    "script_file_count": 0,
                }
            ]
        )
        .execute()
    )
    chapters = [Chapter(**data) for data in chapter_result.data]
    yield projects[0], chapters
