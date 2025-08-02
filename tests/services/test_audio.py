from unittest.mock import patch

import pytest
from pydub import AudioSegment

from bookcast.entities import Chapter, ChapterStatus, Project, ProjectStatus
from bookcast.services.audio import AudioService


class TestAudioServiceIntegration:
    @pytest.mark.integration
    @patch("bookcast.services.audio.CompletedAudioFileService")
    @patch("bookcast.services.audio.TTSFileService")
    def test_generate_audio(self, mock_tts_file_service, mock_completed_audio_file_service):
        project = Project(
            id=1, filename="test_sample.pdf", max_page_number=3, status=ProjectStatus.start_creating_audio
        )
        chapters = [
            Chapter(
                id=1,
                project_id=1,
                chapter_number=1,
                start_page=1,
                end_page=2,
                status=ChapterStatus.start_creating_audio,
                script="Speaker1: Hello there.\nSpeaker2: Hello back.",
            ),
            Chapter(
                id=2,
                project_id=1,
                chapter_number=2,
                start_page=3,
                end_page=3,
                status=ChapterStatus.start_creating_audio,
                script="Speaker1: Goodbye now.\nSpeaker2: See you tomorrow.",
            ),
        ]

        mock_audio_segments = [
            AudioSegment.silent(duration=2000),  # 2秒の無音
            AudioSegment.silent(duration=3000),  # 3秒の無音
        ]
        mock_tts_file_service.read.return_value = mock_audio_segments

        mock_completed_audio_file_service.write.return_value = "/fake/path/output.wav"
        mock_completed_audio_file_service.upload_gcs_from_file.return_value = None

        audio_service = AudioService(audio_resource_directory="tests/resources")

        audio_service.generate_audio(project, chapters)

        assert mock_tts_file_service.read.call_count == 2
        assert mock_completed_audio_file_service.write.call_count == 2
        assert mock_completed_audio_file_service.upload_gcs_from_file.call_count == 2
