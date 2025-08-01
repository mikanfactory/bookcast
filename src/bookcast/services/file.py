import pathlib
import wave
from typing import List

from pydub import AudioSegment

from bookcast.infrastructure.gcs import GCSFileUploadable
from bookcast.path_resolver import (
    build_audio_directory,
    build_script_directory,
    build_text_directory,
    resolve_audio_output_path,
    resolve_audio_path,
    resolve_script_path,
    resolve_text_path,
)


class OCRTextFileService(GCSFileUploadable):
    @classmethod
    def read(cls, filename: str, page_number: int) -> str:
        text_path = resolve_text_path(filename, page_number)
        with open(text_path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    def write(cls, filename: str, page_number: int, content: str) -> pathlib.Path:
        text_dir = build_text_directory(filename)
        text_dir.mkdir(parents=True, exist_ok=True)

        text_path = resolve_text_path(filename, page_number)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(content)

        return text_path

    @classmethod
    def fetch_text_from_gcs(cls, filename: str, page_number: int) -> str:
        text_dir = build_text_directory(filename)
        text_dir.mkdir(parents=True, exist_ok=True)

        text_path = resolve_text_path(filename, page_number)
        return cls._fetch_text_from_gcs(text_path)


class ScriptFileService(GCSFileUploadable):
    @classmethod
    def read(cls, filename: str, chapter_number: int) -> str:
        script_path = resolve_script_path(filename, chapter_number)
        with open(script_path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    def write(cls, filename: str, chapter_number: int, content: str) -> pathlib.Path:
        script_dir = build_script_directory(filename)
        script_dir.mkdir(parents=True, exist_ok=True)

        script_path = resolve_script_path(filename, chapter_number)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(content)

        return script_path


class TTSFileService(GCSFileUploadable):
    @classmethod
    def read(cls, filename: str, chapter_number: int) -> List[AudioSegment]:
        audio_files = []
        index = 0
        while True:
            audio_path = resolve_audio_path(filename, chapter_number, index)
            try:
                audio = AudioSegment.from_wav(audio_path)
                audio_files.append(audio)
                index += 1
            except FileNotFoundError:
                break
        return audio_files

    @classmethod
    def write(cls, filename: str, chapter_number: int, index: int, pcm_data: bytes) -> pathlib.Path:
        audio_dir = build_audio_directory(filename)
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_path = resolve_audio_path(filename, chapter_number, index)
        with wave.open(str(audio_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm_data)

        return audio_path


class AudioFileService(GCSFileUploadable):
    @classmethod
    def read(cls, filename: str, chapter_number: int) -> AudioSegment:
        output_path = resolve_audio_output_path(filename, chapter_number)
        return AudioSegment.from_wav(output_path)

    @classmethod
    def write(cls, filename: str, chapter_number: int, audio: AudioSegment) -> pathlib.Path:
        audio_dir = build_audio_directory(filename)
        audio_dir.mkdir(parents=True, exist_ok=True)

        output_path = resolve_audio_output_path(filename, chapter_number)
        audio.export(output_path, format="wav", bitrate="192k")
        return output_path
