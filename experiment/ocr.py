import click

from bookcast.services.ocr import OCRService


@click.command()
@click.argument("filename", type=str)
def main(filename: str):
    service = OCRService()
    service.process_pdf(filename)


if __name__ == "__main__":
    main()
