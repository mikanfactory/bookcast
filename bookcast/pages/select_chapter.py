import streamlit as st
from streamlit.logger import get_logger
from pathlib import Path
from bookcast.page import Rooter
from bookcast.session_state import SessionState as State


logger = get_logger(__name__)

st.write("select chapter page")

# filename = st.session_state[State.filename]
filename = st.session_state.get(State.filename, "2506.05345.pdf")
if not st.session_state.get(State.page_number):
    st.session_state[State.page_number] = 1

if not st.session_state.get(State.chapters):
    st.session_state[State.chapters] = {}

page_number = st.session_state[State.page_number]
chapters = st.session_state[State.chapters]

col1, col2 = st.columns(2)
with col1:
    file_path = Path(f"downloads/{filename}")
    image_directory = file_path.parent / file_path.stem / "images"
    image_path = image_directory / f"page_{page_number:03d}.png"

    st.image(image_path)

with col2:
    with st.container(height=490):
        text_directory = file_path.parent / file_path.stem / "texts"
        text_path = text_directory / f"page_{page_number:03d}.txt"
        with open(text_path, "r") as f:
            text = f.read()

        st.write(text)


with st.container():
    left, center, right = st.columns(3)
    with left:
        prev_page = st.button("前のページ")
        if prev_page:
            if page_number >= 1:
                st.session_state[State.page_number] = page_number - 1
                st.rerun()

    with center:
        next_page = st.button("次のページ")
        if next_page:
            st.session_state[State.page_number] = page_number + 1
            st.rerun()

    with right:
        set_chapter = st.button("章に設定")
        if set_chapter:
            chapter_counts = len(chapters)
            chapters[chapter_counts + 1] = {
                "title": f"Chapter {chapter_counts + 1}",
                "page_number": page_number,
            }
            st.session_state[State.chapters] = chapters


finish_chapter_setting = st.button("設定完了")
if finish_chapter_setting:
    st.switch_page(Rooter.podcast_setting_page())
