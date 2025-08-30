import io
import time

import requests
import streamlit as st
from streamlit.logger import get_logger

from bookcast.config import BACKEND_URL
from bookcast.page import Rooter
from bookcast.services.image_file import ImageFileService
from bookcast.session_state import SessionState as ss
from bookcast.view_models import ProjectViewModel

logger = get_logger(__name__)


def save_uploaded_file(file_content: memoryview, filename: str):
    logger.info(f"Saving uploaded file: {filename}")

    url = f"{BACKEND_URL}/api/v1/projects/upload_file"

    # Convert memoryview to bytes for proper serialization
    file_bytes = bytes(file_content)

    files = {"file": (filename, file_bytes, "application/pdf")}
    resp = requests.post(url, files=files)
    return resp


def process_uploaded_file(uploaded_file: io.BytesIO):
    file_name = uploaded_file.name

    with st.spinner("Uploading..."):
        logger.info(f"Uploaded file: {file_name}")

        # Save the uploaded file
        resp = save_uploaded_file(uploaded_file.getbuffer(), file_name)
        if resp.ok:
            logger.info(f"Successfully saved file: {file_name}")
            st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        else:
            logger.error(f"Failed to save file: {file_name}")
            logger.error(resp.content)
            st.error("Error Uploading file")

    if resp.ok:
        with st.spinner("Redirecting to project page..."):
            result = resp.json()
            st.session_state[ss.project] = ProjectViewModel(project_id=result["id"])
            image_dir = ImageFileService.convert_pdf_to_images(uploaded_file)
            st.session_state[ss.image_dir] = image_dir

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
