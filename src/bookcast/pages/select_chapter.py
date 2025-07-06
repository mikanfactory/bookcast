import streamlit as st
from streamlit.logger import get_logger

from bookcast.page import Rooter
from bookcast.services import get_service_manager
from bookcast.session_state import ChapterPageSessionState as PState

logger = get_logger(__name__)


def initialize_session(services):
    """Initialize session state and return current values."""
    # Get session values with fallback for debugging
    filename = services.session.get_filename()
    if not filename:
        # デバッグ用のフォールバック
        filename = "2506.05345.pdf"
        services.session.set_filename(filename)

    max_page_number = services.session.get_max_page_number()
    if not max_page_number:
        # デバッグ用のフォールバック
        max_page_number = 23
        services.session.set_max_page_number(max_page_number)

    # Initialize session if needed
    services.session.initialize_session(filename, max_page_number)

    current_page = services.session.get_current_page()
    chapters = services.session.get_chapters()

    return filename, current_page, max_page_number, chapters


def update_chapter(services, current_page: int):
    """Update chapter configuration when user selects a chapter."""
    selected_chapter = st.session_state[PState.chapter_select]
    chapters = services.session.get_chapters()

    # Add chapter using service
    result = services.chapter.add_chapter(chapters, selected_chapter, current_page)

    if result.success:
        # Update session state
        updated_chapters = result.data
        services.session.set_chapters(updated_chapters)
        logger.info(f"Added chapter {selected_chapter} at page {current_page}")
    else:
        st.error(f"Failed to add chapter: {result.error}")


def increment_page(services, current_page: int, max_page_number: int):
    """Move to the next page."""
    if current_page < max_page_number:
        services.session.set_current_page(current_page + 1)


def decrement_page(services, current_page: int):
    """Move to the previous page."""
    if current_page > 1:
        services.session.set_current_page(current_page - 1)


def display_page_content(services, filename: str, current_page: int):
    """Display image and text content for the current page."""
    col1, col2 = st.columns(2)

    with col1:
        # Get image using service
        image_result = services.file.get_image_path(filename, current_page)
        if image_result.success:
            st.image(image_result.data["image_path"])
        else:
            st.error(f"Failed to load image: {image_result.error}")

    with col2:
        with st.container(height=650):
            # Get text content using service
            text_result = services.file.get_text_content(filename, current_page)
            if text_result.success:
                st.write(text_result.data["content"])
            else:
                st.error(f"Failed to load text: {text_result.error}")


def display_navigation_controls(
    services, current_page: int, max_page_number: int, chapters
):
    """Display navigation and chapter selection controls."""
    with st.container():
        left, center, right = st.columns(3, vertical_alignment="bottom")

        with left:
            st.button(
                "前のページ",
                on_click=decrement_page,
                args=(services, current_page),
            )

        with center:
            st.button(
                "次のページ",
                on_click=increment_page,
                args=(services, current_page, max_page_number),
            )

        with right:
            max_chapter = chapters.specified_max_chapter
            st.selectbox(
                "章の選択",
                options=list(range(1, max_chapter + 6)),
                label_visibility="hidden",
                on_change=update_chapter,
                key=PState.chapter_select,
                args=(services, current_page),
                index=None,
                placeholder="章を選択",
            )


def display_chapter_summary(services, chapters):
    """Display summary of configured chapters."""
    with st.expander("設定済みの章", expanded=False):
        summary_result = services.chapter.get_chapter_summary(chapters)
        if summary_result.success:
            st.write(summary_result.data)
        else:
            st.error(f"Failed to get chapter summary: {summary_result.error}")


def validate_and_proceed(services, chapters):
    """Validate chapter configuration and proceed to next page."""
    finish_chapter_setting = st.button("設定完了")
    if finish_chapter_setting:
        validation_result = services.chapter.validate_chapter_config(chapters)

        if validation_result.success:
            logger.info("Chapter configuration validated successfully")
            st.switch_page(Rooter.podcast_setting_page())
        else:
            st.error(validation_result.error)


def main():
    """Main function for the chapter selection page."""
    st.write("select chapter page")

    # Get service manager
    services = get_service_manager()

    # Initialize session and get current state
    filename, current_page, max_page_number, chapters = initialize_session(services)

    # Display page content (image and text)
    display_page_content(services, filename, current_page)

    # Display navigation controls
    display_navigation_controls(services, current_page, max_page_number, chapters)

    # Display chapter summary
    display_chapter_summary(services, chapters)

    # Validate and proceed
    validate_and_proceed(services, chapters)


# Execute main function directly for Streamlit
main()
