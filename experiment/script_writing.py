import json
import logging

import click
from langsmith import tracing_context

from bookcast.entities.chapter import build_chapters
from bookcast.services.script_writing import ScriptWritingService

logger = logging.getLogger(__name__)


@click.command()
@click.argument("config", type=str)
@click.option("--trace", "-t", is_flag=True, default=False)
def main(config: str, trace: bool = False):
    service = ScriptWritingService()

    with open(config, "r") as f:
        config = json.load(f)

    chapters = build_chapters(config)

    logger.info(f"Langsmith tracing enabled: {trace}")
    with tracing_context(enabled=trace):
        service.process(chapters)


if __name__ == "__main__":
    main()
