import logging

import click

from bookcast.entities import Chapter
from bookcast.path_resolver import resolve_text_path
from bookcast.services.script_writing import (
    ScriptWritingService,
)

logger = logging.getLogger(__name__)


def read_text_from_file(filename: str, page_number: int):
    file_path = resolve_text_path(filename, page_number + 1)
    with open(file_path, "r") as f:
        text = f.read()

    return text


def read_texts(filename: str, start_page: int, end_page: int):
    acc = []
    for i in range(start_page, end_page + 1):
        text = read_text_from_file(filename, i)
        acc.append(text)

    return acc


@click.command()
@click.argument("filename", type=str)
def main(filename):
    service = ScriptWritingService()

    texts = read_texts(filename, 0, 36)

    chapter = Chapter(filename=filename, chapter_number=1, extracted_texts=texts)

    service.process(chapter)


if __name__ == "__main__":
    main()
