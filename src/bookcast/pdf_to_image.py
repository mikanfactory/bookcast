import logging
from typing import List

from pdf2image import convert_from_path
from PIL import Image

from bookcast.path_resolver import build_downloads_path, build_image_directory

logger = logging.getLogger(__name__)


def convert_pdf_to_images(filename: str) -> List[Image.Image]:
    pdf_path = build_downloads_path(filename)
    images = convert_from_path(pdf_path)

    image_dir = build_image_directory(filename)
    image_dir.mkdir(parents=True, exist_ok=True)

    for i, image in enumerate(images):
        page_num = 1 + i
        image_filename = image_dir / f"page_{page_num:03d}.png"
        image.save(image_filename, "PNG")

    return images
