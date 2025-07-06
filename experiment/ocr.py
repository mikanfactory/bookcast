from bookcast.ocr import *


async def __combine():
    filename = "プログラマー脳.pdf"
    start_page, end_page = 58, 72

    ocr = GeminiOCR(GEMINI_API_KEY)
    pdf_path = build_downloads_path(filename)

    images = convert_from_path(pdf_path)

    tasks = []
    for n, image in enumerate(images):
        if start_page <= n + 1 <= end_page:
            extracted_text = await ocr.extract_text(filename, n + 1, image)
            print(f"Page {n + 1} extracted text: {extracted_text}")

    await asyncio.gather(*tasks)


def main():
    asyncio.run(__combine())


if __name__ == "__main__":
    main()
