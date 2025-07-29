import wave
from typing import List

from pydub import AudioSegment

from bookcast.path_resolver import (
    build_audio_directory,
    build_script_directory,
    build_text_directory,
    resolve_audio_output_path,
    resolve_audio_path,
    resolve_script_path,
    resolve_text_path,
)


class OCRTextFileService:
    @staticmethod
    def read(filename: str, page_number: int) -> str:
        text_path = resolve_text_path(filename, page_number)
        with open(text_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write(filename: str, page_number: int, content: str) -> None:
        text_dir = build_text_directory(filename)
        text_dir.mkdir(parents=True, exist_ok=True)

        text_path = resolve_text_path(filename, page_number)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(content)


class ScriptFileService:
    @staticmethod
    def read(filename: str, chapter_number: int) -> str:
        script_path = resolve_script_path(filename, chapter_number)
        with open(script_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write(filename: str, chapter_number: int, content: str) -> None:
        script_dir = build_script_directory(filename)
        script_dir.mkdir(parents=True, exist_ok=True)

        script_path = resolve_script_path(filename, chapter_number)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(content)


class TTSFileService:
    @staticmethod
    def read(filename: str, chapter_number: int) -> List[AudioSegment]:
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

    @staticmethod
    def write(filename: str, chapter_number: int, index: int, pcm_data: bytes) -> None:
        audio_dir = build_audio_directory(filename)
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_path = resolve_audio_path(filename, chapter_number, index)
        with wave.open(str(audio_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm_data)


class AudioFileService:
    @staticmethod
    def read(filename: str, chapter_number: int) -> AudioSegment:
        output_path = resolve_audio_output_path(filename, chapter_number)
        return AudioSegment.from_wav(output_path)

    @staticmethod
    def write(filename: str, chapter_number: int, audio: AudioSegment) -> None:
        audio_dir = build_audio_directory(filename)
        audio_dir.mkdir(parents=True, exist_ok=True)

        output_path = resolve_audio_output_path(filename, chapter_number)
        audio.export(output_path, format="wav", bitrate="192k")
