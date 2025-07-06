import time

import streamlit as st
from streamlit.logger import get_logger

from bookcast.page import Rooter
from bookcast.services import get_service_manager

logger = get_logger(__name__)


def main():
    """Main function for the project page."""
    st.write("project page")

    # Get service manager
    services = get_service_manager()

    # File uploader
    uploaded_file = st.file_uploader("Upload a file", type=["pdf"])

    if uploaded_file is not None:
        process_uploaded_file(uploaded_file, services)


def process_uploaded_file(uploaded_file, services):
    """Process the uploaded PDF file."""
    file_name = uploaded_file.name

    with st.spinner("Processing..."):
        logger.info(f"Processing uploaded file: {file_name}")

        # Save the uploaded file
        save_result = services.file.save_uploaded_file(
            uploaded_file.getbuffer(), file_name
        )

        if not save_result.success:
            st.error(f"Failed to save file: {save_result.error}")
            return

        logger.info(f"Successfully saved file: {file_name}")

        # Create project structure
        structure_result = services.file.create_project_structure(file_name)

        if not structure_result.success:
            st.error(f"Failed to create project structure: {structure_result.error}")
            return

        # Process PDF (convert to images and extract text)
        process_result = services.pdf_processing.process_pdf(file_name)

        if not process_result.success:
            st.error(f"Failed to process PDF: {process_result.error}")
            return

        # Update session state
        session_update_result = update_session_state(
            services, file_name, process_result.data
        )

        if not session_update_result.success:
            st.error(f"Failed to update session: {session_update_result.error}")
            return

        logger.info(f"Successfully processed file: {file_name}")

    # Show success message
    st.success(f"File '{uploaded_file.name}' uploaded and processed successfully!")

    # Navigate to next page after a brief delay
    time.sleep(3)
    st.switch_page(Rooter.chapter_page())


def update_session_state(services, file_name, process_data):
    """Update session state with file processing results."""
    try:
        # Set filename
        filename_result = services.session.set_filename(file_name)
        if not filename_result.success:
            return filename_result

        # Set max page number (pages_processed from PDF processing)
        max_page_result = services.session.set_max_page_number(
            process_data["pages_processed"]
        )
        if not max_page_result.success:
            return max_page_result

        # Initialize session with the new values
        init_result = services.session.initialize_session(
            file_name, process_data["pages_processed"]
        )
        if not init_result.success:
            return init_result

        logger.info(f"Session state updated successfully for file: {file_name}")
        return services.session.get_session_summary()

    except Exception as e:
        error_msg = f"Failed to update session state: {str(e)}"
        logger.error(error_msg)
        from bookcast.services.base import ServiceResult

        return ServiceResult.failure(error_msg)


# Execute main function directly for Streamlit
main()
