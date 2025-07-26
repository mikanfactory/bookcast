import click

from bookcast.path_resolver import resolve_script_path, resolve_text_path
from bookcast.services.script_writing import Chapter
from bookcast.services.tts import TextToSpeechService


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
def main(filename: str):
    script_path = resolve_script_path(filename, 1)
    with open(script_path, "r") as f:
        script_text = f.read()

    texts = read_texts(filename, 0, 36)
    chapter = Chapter(filename=filename, chapter_number=1, extracted_texts=texts)

    service = TextToSpeechService()
    service.generate_audio(script_text, chapter)

    # result = service.split_script(script_text)
    # for r in result:
    #     print("*************************************************")
    #     print(r)


if __name__ == "__main__":
    main()
