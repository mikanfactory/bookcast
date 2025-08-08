import streamlit as st
from streamlit.logger import get_logger

from bookcast.page import Rooter
from bookcast.session_state import SessionState as ss
from bookcast.view_models import ChaptersViewModel

logger = get_logger(__name__)


def initialize_session():
    # Get session values with fallback for debugging
    filename = st.session_state.get(ss.filename)
    if not filename:
        filename = "2506.05345.pdf"  # デバッグ用
        st.session_state[ss.filename] = filename

    max_page_number = st.session_state.get(ss.max_page_number)
    if not max_page_number:
        max_page_number = 23  # デバッグ用
        st.session_state[ss.max_page_number] = max_page_number

    current_page = st.session_state.get(ss.current_page)
    chapters = st.session_state.get(ss.chapters)

    return filename, current_page, max_page_number, chapters


def update_chapter(current_page: int):
    selected_chapter = st.session_state[ss.chapter_select]
    chapters = st.session_state[ss.chapters]

    # Add chapter using service
    chapters.add_chapter(selected_chapter, current_page)

    st.session_state[ss.chapters] = chapters
    logger.info(f"Added chapter {selected_chapter} at page {current_page}")


def increment_page(current_page: int, max_page_number: int):
    if current_page < max_page_number:
        st.session_state[ss.current_page] = current_page + 1


def decrement_page(current_page: int):
    if current_page > 1:
        st.session_state[ss.current_page] = current_page - 1


def display_page_content(filename: str, current_page: int):
    col1, col2 = st.columns(2)

    with col1:
        # Get image using service
        image_path = resolve_image_path(filename, current_page)
        st.image(image_path)

    with col2:
        with st.container(height=650):
            # Get text content using service
            text_content = OCRTextFileService.read(filename, current_page)
            st.write(text_content)


def display_navigation_controls(current_page: int, max_page_number: int, chapters: ChaptersViewModel):
    with st.container():
        left, center, right = st.columns(3, vertical_alignment="bottom")

        with left:
            st.button(
                "前のページ",
                on_click=decrement_page,
                args=current_page,
            )

        with center:
            st.button(
                "次のページ",
                on_click=increment_page,
                args=(current_page, max_page_number),
            )

        with right:
            max_chapter = chapters.specified_max_chapter
            st.selectbox(
                "章の選択",
                options=list(range(1, max_chapter + 6)),
                label_visibility="hidden",
                on_change=update_chapter,
                key=ss.chapter_select,
                args=current_page,
                index=None,
                placeholder="章を選択",
            )


def display_chapter_summary(chapters):
    with st.expander("設定済みの章", expanded=False):
        summary_result = chapters.get_chapter_summary()
        st.write(summary_result.data)


def validate_and_proceed(chapters):
    finish_chapter_setting = st.button("設定完了")
    if finish_chapter_setting:
        validation_result = chapters.validate_chapter_config(chapters)

        if validation_result.success:
            logger.info("Chapter configuration validated successfully")
            st.switch_page(Rooter.podcast_page())
        else:
            st.error(validation_result.error)


def main():
    st.write("select chapter page")

    # Initialize session and get current state
    filename, current_page, max_page_number, chapters = initialize_session()

    # Display page content (image and text)
    display_page_content(filename, current_page)

    # Display navigation controls
    display_navigation_controls(current_page, max_page_number, chapters)

    # Display chapter summary
    display_chapter_summary(chapters)

    # Validate and proceed
    validate_and_proceed(chapters)


# Execute main function directly for Streamlit
main()
