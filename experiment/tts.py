import json

import click

from bookcast.entities.chapter import build_chapters
from bookcast.path_resolver import resolve_script_path
from bookcast.services.tts import TextToSpeechService


@click.command()
@click.argument("config", type=str)
def main(config: str):
    with open(config, "r") as f:
        config = json.load(f)

    chapters = build_chapters(config)
    for chapter in chapters:
        script_path = resolve_script_path(chapter.filename, chapter.chapter_number)
        with open(script_path, "r") as f:
            script_text = f.read()

        chapter.script = script_text

    service = TextToSpeechService()
    service.generate_audio(chapters)


if __name__ == "__main__":
    main()
