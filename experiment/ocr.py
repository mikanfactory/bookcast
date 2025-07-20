from bookcast.services.pdf_processing import PDFProcessingService


def main():
    filename = "chapter3.pdf"
    service = PDFProcessingService()

    result = service.process_pdf(filename)
    print(result)


if __name__ == "__main__":
    main()
