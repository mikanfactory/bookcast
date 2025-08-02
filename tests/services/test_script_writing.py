import pytest
from langchain_google_genai import ChatGoogleGenerativeAI

from bookcast.config import GEMINI_API_KEY
from bookcast.services.script_writing import (
    PodcastOrchestrator,
    PodcastScriptEvaluator,
    PodcastScriptWriter,
    PodcastTopicSearcher,
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
