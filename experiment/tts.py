import json

import click

from bookcast.entities.chapter import build_chapters
from bookcast.services.file import ScriptFileService
from bookcast.services.tts import TextToSpeechService


@click.command()
@click.argument("config", type=str)
def main(config: str):
    with open(config, "r") as f:
        config = json.load(f)

    chapters = build_chapters(config)
    for chapter in chapters:
        script_text = ScriptFileService.read(chapter.filename, chapter.chapter_number)
        chapter.script = script_text

    service = TextToSpeechService()
    service.generate_audio(chapters)


if __name__ == "__main__":
    main()
