import time

import streamlit as st
from streamlit.logger import get_logger

from bookcast.page import Rooter
from bookcast.path_resolver import (
    build_downloads_path,
)
from bookcast.services.ocr import OCRService
from bookcast.session_state import SessionState as ss

logger = get_logger(__name__)


def save_uploaded_file(file_content, filename: str):
    logger.info(f"Saving uploaded file: {filename}")

    downloads_path = build_downloads_path(filename)
    downloads_path.parent.mkdir(parents=True, exist_ok=True)

    with open(downloads_path, "wb") as f:
        f.write(file_content)


def process_uploaded_file(uploaded_file):
    file_name = uploaded_file.name

    with st.spinner("Processing..."):
        logger.info(f"Processing uploaded file: {file_name}")

        # Save the uploaded file
        save_uploaded_file(uploaded_file.getbuffer(), file_name)

        logger.info(f"Successfully saved file: {file_name}")

        # Process PDF (convert to images and extract text)
        ocr_service = OCRService()
        max_page_number = ocr_service.process_pdf(file_name)

        st.session_state[ss.filename] = file_name
        st.session_state[ss.max_page_number] = max_page_number
        logger.info(f"Successfully processed file: {file_name}")

    # Show success message
    st.success(f"File '{uploaded_file.name}' uploaded and processed successfully!")

    # Navigate to next page after a brief delay
    time.sleep(3)
    st.switch_page(Rooter.chapter_page())


def main():
    st.write("project page")

    # File uploader
    uploaded_file = st.file_uploader("Upload a file", type=["pdf"])

    if uploaded_file is not None:
        process_uploaded_file(uploaded_file)


# Execute main function directly for Streamlit
main()
