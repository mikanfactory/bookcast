import click

from bookcast.entities import Chapter
from bookcast.services.audio import AudioService


@click.command()
@click.argument("filename", type=str)
def main(filename):
    chapter = Chapter(filename=filename, chapter_number=1, extracted_texts=[])
    service = AudioService()
    service.generate_audio(chapter)


if __name__ == "__main__":
    main()
