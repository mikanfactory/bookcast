import os
import pathlib

import streamlit as st
from streamlit.logger import get_logger

from bookcast.page import Rooter
from bookcast.session_state import SessionState as ss
from bookcast.view_models import ProjectViewModel

logger = get_logger(__name__)

# Constants
DEFAULT_IMAGE_DIR = pathlib.Path("downloads/3654812/images")
BUTTON_STYLE = {"use_container_width": True}


def render_chapter_info(chapter_info, is_compact: bool = False):
    start_text = f"P{chapter_info.start_page_number}" if chapter_info.start_page_number > 0 else "未設定"
    end_text = f"P{chapter_info.end_page_number}" if chapter_info.end_page_number > 0 else "未設定"

    if is_compact:
        st.caption(f"開始: {start_text}")
        st.caption(f"終了: {end_text}")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"開始ページ: {start_text}")
        with col2:
            st.info(f"終了ページ: {end_text}")


def get_current_state():
    image_dir = st.session_state.get(ss.image_dir) or DEFAULT_IMAGE_DIR
    image_files = [image_dir / filename for filename in sorted(os.listdir(image_dir))]

    return {
        "image_files": image_files,
        "max_pages": len(image_files),
        "current_page": st.session_state.get(ss.current_page, 1),
        "project": st.session_state.get(ss.project, ProjectViewModel()),
        "selected_chapter": st.session_state.get(ss.selected_chapter_num)
    }


def navigate_page(direction: int, current_page: int, max_pages: int):
    new_page = current_page + direction
    if 1 <= new_page <= max_pages:
        st.session_state[ss.current_page] = new_page


def set_chapter_page(chapter_num: int, page_num: int, page_type: str, project: ProjectViewModel):
    if page_type == "start":
        project.set_chapter_start_page(chapter_num, page_num)
    else:
        project.set_chapter_end_page(chapter_num, page_num)
    st.session_state[ss.project] = project
    logger.info(f"Set chapter {chapter_num} {page_type} page to {page_num}")
    st.rerun()


def manage_chapters(action: str, project: ProjectViewModel, **kwargs):
    if action == "select":
        chapter_num = kwargs["chapter_num"]
        st.session_state[ss.selected_chapter_num] = chapter_num
        logger.info(f"Selected chapter {chapter_num}")

    elif action == "add":
        if project.chapters:
            new_chapter_num = max(project.chapters.keys()) + 1
            project.add_chapter(new_chapter_num)
        else:
            new_chapter_num = 1
            project.add_chapter(new_chapter_num)
        st.session_state[ss.project] = project
        st.session_state[ss.selected_chapter_num] = new_chapter_num
        logger.info(f"Added new chapter {new_chapter_num}")

    elif action == "remove":
        chapter_num = kwargs["chapter_num"]
        selected_chapter_num = kwargs["selected_chapter_num"]
        project.remove_chapter(chapter_num)
        st.session_state[ss.project] = project
        # If removed chapter was selected, select another one
        if selected_chapter_num == chapter_num:
            if project.chapters:
                st.session_state[ss.selected_chapter_num] = min(project.chapters.keys())
            else:
                st.session_state[ss.selected_chapter_num] = None
        logger.info(f"Removed chapter {chapter_num}")

    return project


def render_page_viewer(image_files: list[str], current_page: int, max_pages: int):
    with st.container(width=400, height=600):
        st.image(image_files[current_page - 1])

    with st.container():
        left, center, right = st.columns(3)
        with left:
            st.button("前のページ", on_click=navigate_page, args=(-1, current_page, max_pages), **BUTTON_STYLE)
        with center:
            st.write(f"ページ {current_page}/{max_pages}")
        with right:
            st.button("次のページ", on_click=navigate_page, args=(1, current_page, max_pages), **BUTTON_STYLE)


def render_single_chapter(project: ProjectViewModel, chapter_num: int, selected_chapter_num: int):
    is_selected = chapter_num == selected_chapter_num
    chapter_info = project.get_chapter_info(chapter_num)

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            button_type = "primary" if is_selected else "secondary"
            if st.button(f"第{chapter_num}章", key=f"select_{chapter_num}", type=button_type, **BUTTON_STYLE):
                manage_chapters("select", project, chapter_num=chapter_num)
                st.rerun()
        with col2:
            if st.button("削除", key=f"remove_{chapter_num}", **BUTTON_STYLE):
                manage_chapters("remove", project, chapter_num=chapter_num, selected_chapter_num=selected_chapter_num)
                st.rerun()

        render_chapter_info(chapter_info, is_compact=True)


def render_chapter_sidebar(project: ProjectViewModel, selected_chapter_num: int):
    with st.sidebar:
        st.header("章管理")

        if st.button("新しい章を追加", **BUTTON_STYLE):
            manage_chapters("add", project)
            st.rerun()

        st.divider()

        if not project.chapters:
            st.info("章を追加してください")
            return

        st.subheader("章一覧")
        for chapter_num in sorted(project.chapters.keys()):
            render_single_chapter(project, chapter_num, selected_chapter_num)


def render_chapter_controls(selected_chapter_num: int, current_page: int, project: ProjectViewModel):
    if selected_chapter_num is None:
        st.info("章を選択してください")
        return

    st.subheader(f"第{selected_chapter_num}章の設定")

    chapter_info = project.get_chapter_info(selected_chapter_num)
    render_chapter_info(chapter_info, is_compact=False)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"開始ページに設定 (P{current_page})", type="primary", **BUTTON_STYLE):
            set_chapter_page(selected_chapter_num, current_page, "start", project)
            st.success(f"開始ページをP{current_page}に設定")

    with col2:
        if st.button(f"終了ページに設定 (P{current_page})", type="secondary", **BUTTON_STYLE):
            set_chapter_page(selected_chapter_num, current_page, "end", project)
            st.success(f"終了ページをP{current_page}に設定")


def render_validation_section(project: ProjectViewModel):
    st.divider()

    with st.expander("章設定の確認", expanded=False):
        summary = project.get_chapter_summary()
        st.write(summary)

    if st.button("設定完了", type="primary", **BUTTON_STYLE):
        try:
            project.validate_chapter_config()
            logger.info("Chapter configuration validated successfully")
            st.switch_page(Rooter.podcast_page())
        except Exception as e:
            st.error(str(e))


def main():
    st.title("章設定")
    st.write("本のページを見ながら、各章の開始ページと終了ページを設定してください。")

    # Get current state
    state = get_current_state()

    # Initialize selected chapter if not set
    if state["selected_chapter"] is None and state["project"].chapters:
        st.session_state[ss.selected_chapter_num] = min(state["project"].chapters.keys())
        state["selected_chapter"] = min(state["project"].chapters.keys())

    # Display sidebar
    render_chapter_sidebar(state["project"], state["selected_chapter"])

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        render_page_viewer(state["image_files"], state["current_page"], state["max_pages"])

    with col2:
        render_chapter_controls(state["selected_chapter"], state["current_page"], state["project"])
        render_validation_section(state["project"])


# Execute main function directly for Streamlit
main()
