import json

import click

from bookcast.entities import build_chapters
from bookcast.services.audio import AudioService


@click.command()
@click.argument("config", type=str)
def main(config):
    with open(config, "r") as f:
        config = json.load(f)

    chapters = build_chapters(config)

    service = AudioService()
    service.generate_audio(chapters)


if __name__ == "__main__":
    main()
