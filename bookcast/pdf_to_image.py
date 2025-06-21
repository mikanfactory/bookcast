import logging
from pathlib import Path
from typing import List
from PIL import Image
from pdf2image import convert_from_path


logger = logging.getLogger(__name__)


def convert_pdf_to_images(filename: str) -> List[Image.Image]:
    pdf_path = Path(f"downloads/{filename}")

    images = convert_from_path(pdf_path)

    output_path = pdf_path.parent / pdf_path.stem
    output_path.mkdir(parents=True, exist_ok=True)

    for i, image in enumerate(images):
        page_num = 1 + i
        image_path = output_path / f"page_{page_num:03d}.png"
        image.save(image_path, "PNG")

    return images
