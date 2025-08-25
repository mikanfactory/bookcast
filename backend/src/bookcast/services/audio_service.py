import pathlib
from logging import getLogger

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from bookcast.entities import Chapter, Project
from bookcast.services.file_service import CompletedAudioFileService, TTSFileService

logger = getLogger(__name__)


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
    def __init__(self, audio_resource_directory: str = "resources"):
        self.audio_resource_directory = pathlib.Path(audio_resource_directory)
        self.jingle_path = self.audio_resource_directory / "jingle.mp3"
        self.opening_call_path = self.audio_resource_directory / "opening_call.wav"
        self.bgm_path = self.audio_resource_directory / "bgm.mp3"

    def _coordinate_jingle(self) -> AudioSegment:
        jingle_audio = AudioSegment.from_mp3(self.jingle_path)
        jingle_audio = normalize(jingle_audio)
        jingle_audio = trim_silence(jingle_audio)

        opening_call = AudioSegment.from_wav(self.opening_call_path)
        opening_call = normalize(opening_call)
        opening_call = trim_silence(opening_call)

        opening = jingle_audio.overlay(opening_call, position=8000)

        return opening

    @staticmethod
    def _coordinate_script(project: Project, chapter: Chapter) -> AudioSegment:
        script_audios = []
        for i in range(chapter.script_file_count):
            logger.info(f"Downloading TTS file for chapter {chapter.chapter_number}, index {i}")
            TTSFileService.download_from_gcs(project.filename, chapter.chapter_number, i)
            audio = TTSFileService.read(project.filename, chapter.chapter_number, i)
            script_audios.append(audio)

        acc = AudioSegment.empty()
        for script_audio in script_audios:
            script_audio = normalize(script_audio)
            script_audio = trim_silence(script_audio)
            acc += script_audio

        return acc

    def _coordinate_bgm(self, script_audio_size: int) -> AudioSegment:
        bgm_audio = AudioSegment.from_mp3(self.bgm_path)
        bgm_looped = (bgm_audio * (script_audio_size // len(bgm_audio) + 1))[:script_audio_size]
        bgm_quiet = bgm_looped - 13
        return bgm_quiet

    def generate_audio(self, project: Project, chapters: list[Chapter]) -> None:
        logger.info("Generating audio for chapters")

        logger.info("Starting audio generation")
        jingle_audio = self._coordinate_jingle()

        for chapter in chapters:
            script_audio = self._coordinate_script(project, chapter)
            bgm_audio = self._coordinate_bgm(len(script_audio))
            script_with_bgm = script_audio.overlay(bgm_audio)
            output_audio = jingle_audio + script_with_bgm

            source_file_path = CompletedAudioFileService.write(project.filename, chapter.chapter_number, output_audio)
            CompletedAudioFileService.upload_gcs_from_file(source_file_path)

        logger.info("Audio generation completed successfully.")
