from unittest.mock import patch

import pytest
from pydub import AudioSegment

from bookcast.entities import Chapter, ChapterStatus, Project, ProjectStatus
from bookcast.services import audio_service
from bookcast.services.audio_service import AudioService


class TestAudioServiceIntegration:
    @pytest.mark.integration
    @patch.object(audio_service, "CompletedAudioFileService")
    @patch.object(audio_service, "TTSFileService")
    def test_generate_audio(self, mock_tts_file_service, mock_completed_audio_file_service):
        project = Project(id=1, filename="test_sample.pdf", status=ProjectStatus.start_creating_audio)
        chapters = [
            Chapter(
                id=1,
                project_id=1,
                chapter_number=1,
                start_page=1,
                end_page=2,
                status=ChapterStatus.start_creating_audio,
                script="Speaker1: Hello there.\nSpeaker2: Hello back.",
                script_file_count=1,
            ),
            Chapter(
                id=2,
                project_id=1,
                chapter_number=2,
                start_page=3,
                end_page=3,
                status=ChapterStatus.start_creating_audio,
                script="Speaker1: Goodbye now.\nSpeaker2: See you tomorrow.",
                script_file_count=1,
            ),
        ]

        mock_audio_segments = AudioSegment.silent(duration=2000)
        mock_tts_file_service.bulk_download_from_gcs.return_value = ["/fake/path1.wav"]
        mock_tts_file_service.read_from_path.return_value = mock_audio_segments

        mock_completed_audio_file_service.write.return_value = "/fake/path/output.wav"
        mock_completed_audio_file_service.upload_gcs_from_file.return_value = None

        audio_service = AudioService(audio_resource_directory="tests/resources")

        audio_service.generate_audio(project, chapters)

        assert mock_tts_file_service.bulk_download_from_gcs.call_count == 2
        assert mock_tts_file_service.read_from_path.call_count == 2
        assert mock_completed_audio_file_service.write.call_count == 2
        assert mock_completed_audio_file_service.upload_gcs_from_file.call_count == 2
