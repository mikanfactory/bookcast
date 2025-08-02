from unittest.mock import patch

import pytest

from bookcast.entities import Chapter, ChapterStatus, Project, ProjectStatus, TTSWorkerResult
from bookcast.services.tts import TextToSpeechService


class TestTextToSpeechServiceIntegration:
    @pytest.mark.integration
    @patch("bookcast.services.tts.TTSFileService")
    def test_generate_audio(self, mock_tts_file_service):
        project = Project(id=1, filename="test_sample.pdf", max_page_number=3, status=ProjectStatus.start_tts)
        chapters = [
            Chapter(
                id=1,
                project_id=1,
                chapter_number=1,
                start_page=1,
                end_page=3,
                status=ChapterStatus.start_tts,
                script=(
                    "Speaker1: こんにちは。今日は面白い内容ですね。\nSpeaker2: 本当ですね。詳しく説明していきましょう。"
                ),
            )
        ]

        mock_tts_file_service.write.return_value = "/fake/path/audio.wav"
        mock_tts_file_service.upload_gcs_from_file.return_value = None

        tts_service = TextToSpeechService()

        with patch.object(tts_service, "_invoke", return_value=b"fake_audio_data"):
            results = tts_service.generate_audio(project, chapters)

        assert isinstance(results, list)
        assert isinstance(results[0], TTSWorkerResult)

        mock_tts_file_service.write.assert_called_once_with("test_sample.pdf", 1, 0, b"fake_audio_data")
        mock_tts_file_service.upload_gcs_from_file.assert_called_once_with("/fake/path/audio.wav")

    class TestSplitScript:
        def test_long_text(self):
            long_script = (
                "Speaker1: " + "This is a very long script. " * 1000 + "\nSpeaker2: Yes, it is very long indeed."
            )

            chunks = TextToSpeechService.split_script(long_script)

            assert isinstance(chunks, list)
            assert len(chunks) > 1

        def test_short_text(self):
            short_script = "Speaker1: こんにちは。\nSpeaker2: こんにちは。"

            chunks = TextToSpeechService.split_script(short_script)

            assert isinstance(chunks, list)
            assert len(chunks) == 1
            assert chunks[0] == short_script
