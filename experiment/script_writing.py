import logging

from bookcast.services.podcast import PodcastService, Chapter, PodcastSetting
from bookcast.path_resolver import (resolve_text_path)

logger = logging.getLogger(__name__)


def read_text_from_file(filename: str, page_number: int):
    file_path = resolve_text_path(filename, 1)
    with open(file_path, "r") as f:
        text = f.read()

    return text


def read_texts(filename: str, start_page: int, end_page: int):
    acc = []
    for i in range(start_page, end_page + 1):
        text = read_text_from_file(filename, i)
        acc.append(text)

    return acc


def main():
    filename = "chapter3.pdf"
    service = PodcastService()

    podcast_setting = PodcastSetting(
        num_of_people=2,
        personality1_name='Alnilam',
        personality2_name='Autonoe',
        length=15,
        prompt=None
    )

    texts = read_texts(filename, 0, 37)

    chapter = Chapter(
        filename=filename,
        chapter_number=1,
        extracted_texts=texts
    )

    result = service.process(podcast_setting, chapter)
    print(result)


if __name__ == "__main__":
    main()
