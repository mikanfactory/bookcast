from bookcast.services.ocr import OCRService


def main():
    filename = "chapter3.pdf"
    service = OCRService()

    result = service.process_pdf(filename)
    print(result)


if __name__ == "__main__":
    main()
