import pathlib
import wave

from pydub import AudioSegment

from bookcast.infrastructure.gcs import GCSFileUploadable


def build_downloads_path(filename: str) -> pathlib.Path:
    return pathlib.Path(f"downloads/{filename}")


def build_book_directory(filename: str) -> pathlib.Path:
    file_path = build_downloads_path(filename)
    return file_path.parent / file_path.stem


def build_image_directory(filename: str) -> pathlib.Path:
    base_path = build_book_directory(filename)
    return base_path / "images"


def build_text_directory(filename: str) -> pathlib.Path:
    base_path = build_book_directory(filename)
    return base_path / "texts"


def build_script_directory(filename: str) -> pathlib.Path:
    base_path = build_book_directory(filename)
    return base_path / "scripts"


def build_audio_directory(filename: str) -> pathlib.Path:
    base_path = build_book_directory(filename)
    return base_path / "audio"


def build_completed_audio_directory(filename: str) -> pathlib.Path:
    base_path = build_book_directory(filename)
    return base_path / "completed_audio"


def resolve_book_path(filename: str) -> pathlib.Path:
    return build_book_directory(filename) / filename


def resolve_image_path(filename: str, page_number: int) -> pathlib.Path:
    image_dir = build_image_directory(filename)
    return image_dir / f"page_{page_number:03d}.png"


def resolve_text_path(filename: str, page_number: int) -> pathlib.Path:
    text_dir = build_text_directory(filename)
    return text_dir / f"page_{page_number:03d}.txt"


def resolve_script_path(filename: str, chapter_num: int) -> pathlib.Path:
    script_dir = build_script_directory(filename)
    return script_dir / f"chapter_{chapter_num:03d}_script.txt"


def resolve_audio_path(filename: str, chapter_num: int, index: int) -> pathlib.Path:
    script_dir = build_audio_directory(filename)
    return script_dir / f"chapter_{chapter_num:03d}_{index}_script.wav"


def resolve_audio_output_path(filename: str, chapter_num: int) -> pathlib.Path:
    audio_dir = build_completed_audio_directory(filename)
    return audio_dir / f"chapter_{chapter_num:03d}_output.wav"


class OCRImageFileService(GCSFileUploadable):
    @classmethod
    def read(cls, filename: str) -> bytes:
        image_path = resolve_book_path(filename)
        with open(image_path, "rb") as f:
            return f.read()

    @classmethod
    def write(cls, filename: str, image_data: bytes) -> pathlib.Path:
        book_dir = build_book_directory(filename)
        book_dir.mkdir(parents=True, exist_ok=True)

        book_path = resolve_book_path(filename)
        with open(book_path, "wb") as f:
            f.write(image_data)

        return book_path

    @classmethod
    def download_from_gcs(cls, filename: str) -> pathlib.Path:
        book_dir = build_book_directory(filename)
        book_dir.mkdir(parents=True, exist_ok=True)

        book_path = resolve_book_path(filename)
        cls._download_from_gcs(book_path)
        return book_path


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
    def read(cls, filename: str, chapter_number: int, index: int) -> AudioSegment:
        audio_path = resolve_audio_path(filename, chapter_number, index)
        return AudioSegment.from_wav(audio_path)

    @classmethod
    def read_from_path(cls, audio_path: pathlib.Path) -> AudioSegment:
        return AudioSegment.from_wav(audio_path)

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

    @classmethod
    def download_from_gcs(cls, filename: str, chapter_number: int, index: int) -> pathlib.Path:
        audio_dir = build_audio_directory(filename)
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_path = resolve_audio_path(filename, chapter_number, index)
        cls._download_from_gcs(audio_path)
        return audio_path

    @classmethod
    async def bulk_download_from_gcs(
        cls, filename: str, chapter_number: int, script_file_count: int
    ) -> list[pathlib.Path]:
        audio_dir = build_audio_directory(filename)
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_paths = [resolve_audio_path(filename, chapter_number, index) for index in range(script_file_count)]
        await cls._bulk_download_from_gcs(audio_paths)
        return audio_paths


class CompletedAudioFileService(GCSFileUploadable):
    @classmethod
    def read(cls, filename: str, chapter_number: int) -> AudioSegment:
        output_path = resolve_audio_output_path(filename, chapter_number)
        return AudioSegment.from_wav(output_path)

    @classmethod
    def write(cls, filename: str, chapter_number: int, audio: AudioSegment) -> pathlib.Path:
        audio_dir = build_completed_audio_directory(filename)
        audio_dir.mkdir(parents=True, exist_ok=True)

        output_path = resolve_audio_output_path(filename, chapter_number)
        audio.export(output_path, format="wav", bitrate="192k")
        return output_path

    @classmethod
    def download_from_gcs(cls, filename: str, chapter_number: int) -> pathlib.Path:
        audio_dir = build_completed_audio_directory(filename)
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_path = resolve_audio_output_path(filename, chapter_number)
        cls._download_from_gcs(audio_path)
        return audio_path
