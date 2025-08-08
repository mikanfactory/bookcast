import io

from PIL import Image
from pdf2image import convert_from_path


class ImageFileService:

    @staticmethod
    def convert_pdf_to_images(file: io.BytesIO) -> list[Image.Image]:
        file_path = f"downloads/{file.name}"
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())

        images = convert_from_path(file_path)
        return images
