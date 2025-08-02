import pytest
from langchain_google_genai import ChatGoogleGenerativeAI

from bookcast.config import GEMINI_API_KEY
from bookcast.services.ocr import OCRExecutor, OCROrchestrator, OCRResultEditor


@pytest.fixture
def llm():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, temperature=0.01)


def test_ocr_executor(llm):
    ocr_executor = OCRExecutor(llm)
    assert ocr_executor


def test_ocr_result_editor(llm):
    ocr_editor = OCRResultEditor(llm)
    assert ocr_editor


def test_ocr_orchestrator(llm):
    orchestrator = OCROrchestrator(llm)
    assert orchestrator
