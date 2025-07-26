from logging import getLogger
from typing import Optional

import click
from langsmith import tracing_context

from bookcast.services.ocr import OCRService

logger = getLogger(__name__)


@click.command()
@click.argument("filename", type=str)
@click.option("--page_number", "-p", type=int)
@click.option("--trace", "-t", is_flag=True, default=False)
def main(filename: str, page_number: Optional[int] = None, trace: bool = False):
    service = OCRService()
    logger.info(f"Langsmith tracing enabled: {trace}")
    with tracing_context(enabled=trace):
        service.process_pdf(filename, page_number)


if __name__ == "__main__":
    main()
