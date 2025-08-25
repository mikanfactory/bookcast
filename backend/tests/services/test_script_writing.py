from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_google_genai import ChatGoogleGenerativeAI

from bookcast.config import GEMINI_API_KEY
from bookcast.entities import Chapter, ChapterStatus, Project, ProjectStatus
from bookcast.services import script_writing_service
from bookcast.services.script_writing_service import (
    PodcastOrchestrator,
    PodcastScriptEvaluator,
    PodcastScriptWriter,
    PodcastTopicSearcher,
    ScriptWritingService,
)


@pytest.fixture
def llm():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01)


def test_podcast_topic_searcher(llm):
    ocr_executor = PodcastTopicSearcher(llm)
    assert ocr_executor


def test_podcast_script_writer(llm):
    ocr_editor = PodcastScriptWriter(llm)
    assert ocr_editor


def test_podcast_script_evaluator(llm):
    orchestrator = PodcastScriptEvaluator(llm)
    assert orchestrator


def test_podcast_orchestrator(llm):
    orchestrator = PodcastOrchestrator(llm)
    assert orchestrator


class TestScriptWritingServiceIntegration:
    @pytest.mark.integration
    @patch.object(script_writing_service, "PodcastOrchestrator")
    async def test_process(self, mock_orchestrator_class):
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

        mock_orchestrator = AsyncMock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.run.return_value = (
            "Speaker1: こんにちは。今日は面白い内容ですね。\nSpeaker2: 本当ですね。詳しく説明していきましょう。"
        )

        mock_chapter_service = MagicMock()
        script_writing_service = ScriptWritingService(mock_chapter_service)
        await script_writing_service.process(project, chapters)

        mock_orchestrator.run.assert_called_once_with("This is extracted text from the chapter.")
        mock_chapter_service.update.assert_called_once()
