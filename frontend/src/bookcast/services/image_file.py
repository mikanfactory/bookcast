import io
import pathlib

from pdf2image import convert_from_bytes, convert_from_path
from PIL import Image


class ImageFileService:
    @staticmethod
    def read_pdf(filename: str) -> list[Image.Image]:
        file_path = f"downloads/{filename}"
        images = convert_from_path(file_path)
        return images

    @staticmethod
    def convert_pdf_to_images(file: io.BytesIO) -> pathlib.Path:
        file_dir = pathlib.Path("downloads") / pathlib.Path(file.name).stem
        file_dir.mkdir(parents=True, exist_ok=True)

        image_dir = file_dir / "images"
        image_dir.mkdir(parents=True, exist_ok=True)

        convert_from_bytes(file.getvalue(), output_folder=image_dir, fmt="png", output_file="page", thread_count=8)
        return image_dir
