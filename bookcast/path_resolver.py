from pathlib import Path


def build_downloads_path(filename: str) -> Path:
    return Path(f"downloads/{filename}")


def build_book_directory(filename: str) -> Path:
    file_path = build_downloads_path(filename)
    return file_path.parent / file_path.stem


def build_image_directory(filename: str) -> Path:
    base_path = build_book_directory(filename)
    return base_path / "images"


def build_text_directory(filename: str) -> Path:
    base_path = build_book_directory(filename)
    return base_path / "texts"


def resolve_image_path(filename: str, page_number: int) -> Path:
    image_dir = build_image_directory(filename)
    return image_dir / f"page_{page_number:03d}.png"


def resolve_text_path(filename: str, page_number: int) -> Path:
    text_dir = build_text_directory(filename)
    return text_dir / f"page_{page_number:03d}.txt"
