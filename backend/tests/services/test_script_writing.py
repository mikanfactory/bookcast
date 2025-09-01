from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_google_genai import ChatGoogleGenerativeAI

from bookcast.config import GEMINI_API_KEY
from bookcast.entities import Chapter, ChapterStatus, Project, ProjectStatus
from bookcast.services import script_writing_service
from bookcast.services.script_writing_service import (
    ScriptWritingService,
    search_topics,
    write_script,
    evaluate_script,
    script_writing_workflow,
)


@pytest.fixture
def llm():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01)


def test_search_topics_task():
    assert search_topics


def test_write_script_task():
    assert write_script


def test_evaluate_script_task():
    assert evaluate_script


def test_script_writing_workflow():
    assert script_writing_workflow


class TestScriptWritingServiceIntegration:
    @pytest.mark.integration
    @patch.object(script_writing_service, "script_writing_workflow")
    async def test_process(self, mock_workflow):
        project = Project(id=1, filename="test_sample.pdf", status=ProjectStatus.start_writing_script)
        chapters = [
            Chapter(
                id=1,
                project_id=1,
                chapter_number=1,
                start_page=1,
                end_page=3,
                status=ChapterStatus.start_writing_script,
                extracted_text="This is extracted text from the chapter.",
            )
        ]

        mock_workflow.ainvoke = AsyncMock()
        mock_workflow.ainvoke.return_value = (
            "Speaker1: こんにちは。今日は面白い内容ですね。\nSpeaker2: 本当ですね。詳しく説明していきましょう。"
        )

        mock_chapter_service = MagicMock()
        script_writing_service_instance = ScriptWritingService(mock_chapter_service)
        await script_writing_service_instance.process(project, chapters)

        mock_workflow.ainvoke.assert_called_once()
        mock_chapter_service.update.assert_called_once()
