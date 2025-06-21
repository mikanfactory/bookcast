import streamlit as st
from streamlit.logger import get_logger
from pathlib import Path
from bookcast.page import Rooter
from bookcast.session_state import SessionState as State

from pydantic import BaseModel

logger = get_logger(__name__)


class ChapterConfig(BaseModel):
    page_number: int


class Chapters(BaseModel):
    specified_max_chapter: int = 1
    chapters: dict[int, ChapterConfig] = {}


def initialise():
    # filename = st.session_state[State.filename]
    # max_page_number = st.session_state[State.max_page_number]

    # デバッグ用
    filename = st.session_state.get(State.filename, "2506.05345.pdf")
    max_page_number = st.session_state.get(State.max_page_number, 23)

    if not st.session_state.get(State.page_number):
        st.session_state[State.page_number] = 1

    if not st.session_state.get(State.chapters):
        st.session_state[State.chapters] = Chapters()

    page_number = st.session_state[State.page_number]
    chapters = st.session_state[State.chapters]

    return filename, page_number, max_page_number, chapters


def update_chapter(chapters: Chapters, page_number: int):
    selected_chapter = st.session_state["chapter_select"]
    config = ChapterConfig(page_number=page_number)

    chapters.chapters[selected_chapter] = config
    chapters.specified_max_chapter = max(
        chapters.specified_max_chapter, selected_chapter
    )

    st.session_state[State.chapters] = chapters


def increment_page(page_number: int, max_page_number: int):
    if page_number < max_page_number:
        st.session_state[State.page_number] = page_number + 1


def decrement_page(page_number: int):
    if page_number >= 1:
        st.session_state[State.page_number] = page_number - 1


def validate_chapter_config(chapters: Chapters):
    pass


def main():
    filename, page_number, max_page_number, chapters = initialise()
    st.write("select chapter page")

    col1, col2 = st.columns(2)
    with col1:
        file_path = Path(f"downloads/{filename}")
        image_directory = file_path.parent / file_path.stem / "images"
        image_path = image_directory / f"page_{page_number:03d}.png"

        st.image(image_path)

    with col2:
        with st.container(height=600):
            text_directory = file_path.parent / file_path.stem / "texts"
            text_path = text_directory / f"page_{page_number:03d}.txt"
            with open(text_path, "r") as f:
                text = f.read()

            st.write(text)

    with st.container():
        left, center, right = st.columns(3)
        with left:
            st.button("前のページ", on_click=decrement_page, args=(page_number,))

        with center:
            st.button(
                "次のページ",
                on_click=increment_page,
                args=(page_number, max_page_number),
            )

        with right:
            max_chapter = chapters.specified_max_chapter
            st.selectbox(
                "章の選択",
                options=list(range(1, max_chapter + 6)),
                label_visibility="hidden",
                on_change=update_chapter,
                key="chapter_select",
                args=(chapters, page_number),
                index=None,
            )

    finish_chapter_setting = st.button("設定完了")
    if finish_chapter_setting:
        if validate_chapter_config(chapters):
            st.switch_page(Rooter.podcast_setting_page())
        else:
            st.error("章の設定に問題があります。確認してください。")


if __name__ == "__main__":
    main()
