import time

import streamlit as st
from streamlit.logger import get_logger
from bookcast.page import Rooter
from bookcast.pdf_to_image import convert_pdf_to_images
from bookcast.ocr import extract_text
from bookcast.session_state import SessionState as State

logger = get_logger(__name__)

st.write("project page")

uploaded_file = st.file_uploader("Upload a file", type=["pdf"])
if uploaded_file is not None:
    with st.spinner("Processing..."):
        file_name = uploaded_file.name
        logger.info(f"Save file: {file_name}")
        with open(f"downloads/{file_name}", "wb") as f:
            f.write(uploaded_file.getbuffer())

        logger.info(f"Converting PDF to images for file: {file_name}")
        images = convert_pdf_to_images(file_name)
        st.session_state[State.max_page_number] = len(images) + 1

        logger.info(f"Extracting text from images for file: {file_name}")
        extract_text(file_name)

    st.success(f"File '{uploaded_file.name}' uploaded successfully!")
    st.session_state[State.filename] = file_name
    time.sleep(3)
    st.switch_page(Rooter.chapter_page())
