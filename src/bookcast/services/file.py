from bookcast.path_resolver import build_text_directory, resolve_text_path


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
    pass


class TTSFileService:
    pass


class AudioFileService:
    pass
