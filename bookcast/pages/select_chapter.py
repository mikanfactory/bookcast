import streamlit as st
from streamlit.logger import get_logger
from bookcast.path_resolver import resolve_text_path, resolve_image_path
from bookcast.page import Rooter
from bookcast.session_state import SessionState as State
from bookcast.session_state import ChapterPageSessionState as PState

from pydantic import BaseModel

logger = get_logger(__name__)


class ChapterConfig(BaseModel):
    page_number: int


class Chapters(BaseModel):
    specified_max_chapter: int = 1
    chapters: dict[int, ChapterConfig] = {}


def initialize():
    # filename = st.session_state[State.filename]
    # max_page_number = st.session_state[State.max_page_number]

    # デバッグ用
    filename = st.session_state.get(State.filename, "2506.05345.pdf")
    max_page_number = st.session_state.get(State.max_page_number, 23)

    if not st.session_state.get(PState.current_page):
        st.session_state[PState.current_page] = 1

    if not st.session_state.get(State.chapters):
        st.session_state[State.chapters] = Chapters()

    current_page = st.session_state[PState.current_page]
    chapters = st.session_state[State.chapters]

    return filename, current_page, max_page_number, chapters


def update_chapter(chapters: Chapters, current_page: int):
    selected_chapter = st.session_state[PState.chapter_select]
    config = ChapterConfig(page_number=current_page)

    chapters.chapters[selected_chapter] = config
    chapters.specified_max_chapter = max(
        chapters.specified_max_chapter, selected_chapter
    )

    st.session_state[State.chapters] = chapters


def increment_page(current_page: int, max_page_number: int):
    if current_page < max_page_number:
        st.session_state[PState.current_page] = current_page + 1


def decrement_page(current_page: int):
    if current_page >= 1:
        st.session_state[PState.current_page] = current_page - 1


def validate_chapter_config(chapters: Chapters) -> bool:
    specified_max_chapter = chapters.specified_max_chapter
    if chapters.chapters == {}:
        st.error("章が選択されていません。1つ以上選択してください。")
        return False

    if len(chapters.chapters) < specified_max_chapter:
        not_filled_chapters = []
        expected = range(1, specified_max_chapter)
        actual = chapters.chapters.keys()
        for c in expected:
            if c not in actual:
                not_filled_chapters.append(c)

        text = "章の設定が不完全です。すべての章を設定してください。\n\n"
        text += "設定されていない章: " + ", ".join(map(str, not_filled_chapters))
        st.error(text)
        return False

    specified_pages = set()
    duplicates = []
    for chapter_num, config in chapters.chapters.items():
        if config.page_number not in specified_pages:
            specified_pages.add(config.page_number)
        else:
            duplicates.append(config.page_number)

    if duplicates:
        text = "ページ番号の重複があります。以下のページ番号が重複しています:\n\n"
        text += ", ".join(map(str, duplicates))
        st.error(text)
        return False

    return True


def main():
    filename, current_page, max_page_number, chapters = initialize()
    st.write("select chapter page")

    col1, col2 = st.columns(2)
    with col1:
        image_path = resolve_image_path(filename, current_page)
        st.image(image_path)

    with col2:
        with st.container(height=650):
            text_path = resolve_text_path(filename, current_page)
            with open(text_path, "r") as f:
                text = f.read()

            st.write(text)

    with st.container():
        left, center, right = st.columns(3, vertical_alignment="bottom")
        with left:
            st.button("前のページ", on_click=decrement_page, args=(current_page,))

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
                key=PState.chapter_select,
                args=(chapters, current_page),
                index=None,
                placeholder="章を選択",
            )

    with st.expander("設定済みの章", expanded=False):
        if chapters.chapters:
            text = ""
            for k, v in chapters.chapters.items():
                text += f"第{k}章: ページ {v.page_number}\n\n\n"

            st.write(text)
        else:
            st.write("設定された章はありません。")

    finish_chapter_setting = st.button("設定完了")
    if finish_chapter_setting:
        if validate_chapter_config(chapters):
            st.switch_page(Rooter.podcast_setting_page())


if __name__ == "__main__":
    main()
