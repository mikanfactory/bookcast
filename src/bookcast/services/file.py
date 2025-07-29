from bookcast.path_resolver import (
    build_script_directory,
    build_text_directory,
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
    pass


class AudioFileService:
    pass
