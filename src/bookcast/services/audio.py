from logging import getLogger

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from bookcast.entities import Chapter, ChapterStatus, Project, ProjectStatus
from bookcast.repositories import ChapterRepository, ProjectRepository
from bookcast.services.db import supabase_client
from bookcast.services.file import AudioFileService, TTSFileService

logger = getLogger(__name__)

chapter_repository = ChapterRepository(supabase_client)
project_repository = ProjectRepository(supabase_client)


def normalize(audio: AudioSegment, target_dBFS=-16.0):
    change_in_dBFS = target_dBFS - audio.dBFS
    return audio.apply_gain(change_in_dBFS)


def trim_silence(audio: AudioSegment, silence_thresh=-40, min_silence_len=500):
    nonsilent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    if not nonsilent_ranges:
        return audio
    start_trim = nonsilent_ranges[0][0]
    end_trim = nonsilent_ranges[-1][1]
    return audio[start_trim:end_trim]


class AudioService:
    @staticmethod
    def _coordinate_jingle() -> AudioSegment:
        jingle_audio = AudioSegment.from_mp3("resources/jingle.mp3")
        jingle_audio = normalize(jingle_audio)
        jingle_audio = trim_silence(jingle_audio)

        opening_call = AudioSegment.from_wav("resources/opening_call.wav")
        opening_call = normalize(opening_call)
        opening_call = trim_silence(opening_call)

        opening = jingle_audio.overlay(opening_call, position=8000)

        return opening

    @staticmethod
    def _coordinate_script(chapter: Chapter) -> AudioSegment:
        script_audios = TTSFileService.read(chapter.filename, chapter.chapter_number)
        acc = AudioSegment.empty()
        for script_audio in script_audios:
            script_audio = normalize(script_audio)
            script_audio = trim_silence(script_audio)
            acc += script_audio

        return acc

    @staticmethod
    def _coordinate_bgm(script_audio_size: int) -> AudioSegment:
        bgm_audio = AudioSegment.from_mp3("resources/bgm.mp3")
        bgm_looped = (bgm_audio * (script_audio_size // len(bgm_audio) + 1))[:script_audio_size]
        bgm_quiet = bgm_looped - 13
        return bgm_quiet

    @staticmethod
    def _update_status(project: Project, chapters: list[Chapter]) -> None:
        project.status = ProjectStatus.start_creating_audio
        project_repository.update(project)

        for chapter in chapters:
            chapter.status = ChapterStatus.start_creating_audio
            chapter_repository.update(chapter)

    @staticmethod
    def _update_to_completed(project: Project, chapters: list[Chapter]) -> None:
        project.status = ProjectStatus.creating_audio_completed
        project_repository.update(project)

        for chapter in chapters:
            chapter.status = ChapterStatus.creating_audio_completed
            chapter_repository.update(chapter)

    def generate_audio(self, project: Project, chapters: list[Chapter]) -> None:
        logger.info("Generating audio for chapters")
        self._update_status(project, chapters)

        jingle_audio = self._coordinate_jingle()

        for chapter in chapters:
            script_audio = self._coordinate_script(chapter)
            bgm_audio = self._coordinate_bgm(len(script_audio))
            script_with_bgm = script_audio.overlay(bgm_audio)
            output_audio = jingle_audio + script_with_bgm

            AudioFileService.write(chapter.filename, chapter.chapter_number, output_audio)

        self._update_to_completed(project, chapters)
        logger.info("Audio generation completed successfully.")
