import pytest
from unittest.mock import Mock
import base64

from bookcast.services.pdf_processing import OCRExecutorAgent, OCRState


class TestOCRExecutorAgent:
    @pytest.fixture
    def mock_llm(self):
        mock_llm = Mock()
        mock_llm.with_structured_output = Mock()
        return mock_llm

    @pytest.fixture
    def ocr_agent(self, mock_llm):
        return OCRExecutorAgent(mock_llm)

    @pytest.fixture
    def sample_base64_image(self):
        return base64.b64encode(b"fake_image_data").decode('utf-8')

    @pytest.fixture
    def sample_ocr_state(self, sample_base64_image):
        return OCRState(base64_image=sample_base64_image)

    @pytest.mark.asyncio
    async def test_run_successful_ocr(self, ocr_agent, sample_ocr_state, mock_llm):
        result = await ocr_agent.run(sample_ocr_state)
