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
    filename, page_number, max_page_number, chapters = initialise()
    st.write("select chapter page")

    col1, col2 = st.columns(2)
    with col1:
        file_path = Path(f"downloads/{filename}")
        image_directory = file_path.parent / file_path.stem / "images"
        image_path = image_directory / f"page_{page_number:03d}.png"

        st.image(image_path)

    with col2:
        with st.container(height=650):
            text_directory = file_path.parent / file_path.stem / "texts"
            text_path = text_directory / f"page_{page_number:03d}.txt"
            with open(text_path, "r") as f:
                text = f.read()

            st.write(text)

    with st.container():
        left, center, right = st.columns(3, vertical_alignment='bottom')
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
