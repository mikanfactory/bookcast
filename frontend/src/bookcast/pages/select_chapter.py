import os
import pathlib

import streamlit as st
from streamlit.logger import get_logger

from bookcast.page import Rooter
from bookcast.session_state import SessionState as ss
from bookcast.view_models import ProjectViewModel

logger = get_logger(__name__)


def initialize_session():
    image_dir = st.session_state.get(ss.image_dir, None)
    if not image_dir:
        image_dir = pathlib.Path("downloads/3654812/images")  # デバッグ用

    image_files = [image_dir / filename for filename in sorted(os.listdir(image_dir))]
    max_page_number = len(image_files)

    current_page = st.session_state.get(ss.current_page, 1)
    project = st.session_state.get(ss.project, ProjectViewModel())
    selected_chapter_num = st.session_state.get(ss.selected_chapter_num)

    return image_files, max_page_number, current_page, project, selected_chapter_num


def select_chapter(chapter_num: int):
    st.session_state[ss.selected_chapter_num] = chapter_num
    logger.info(f"Selected chapter {chapter_num}")


def add_new_chapter(project):
    if project and project.chapters:
        new_chapter_num = max(project.chapters.keys()) + 1
        project.add_chapter(new_chapter_num)
    else:
        project = ProjectViewModel()
        new_chapter_num = 1
        project.add_chapter(new_chapter_num)

    st.session_state[ss.project] = project
    st.session_state[ss.selected_chapter_num] = new_chapter_num
    logger.info(f"Added new chapter {new_chapter_num}")


def remove_chapter(chapter_num: int, project, selected_chapter_num):
    project.remove_chapter(chapter_num)
    st.session_state[ss.project] = project

    # If removed chapter was selected, select another one
    if selected_chapter_num == chapter_num:
        if project.chapters:
            st.session_state[ss.selected_chapter_num] = min(project.chapters.keys())
        else:
            st.session_state[ss.selected_chapter_num] = None

    logger.info(f"Removed chapter {chapter_num}")


def set_chapter_start_page(chapter_num: int, page_num: int, project):
    project.set_chapter_start_page(chapter_num, page_num)
    st.session_state[ss.project] = project
    logger.info(f"Set chapter {chapter_num} start page to {page_num}")


def set_chapter_end_page(chapter_num: int, page_num: int, project):
    project.set_chapter_end_page(chapter_num, page_num)
    st.session_state[ss.project] = project
    logger.info(f"Set chapter {chapter_num} end page to {page_num}")


def increment_page(current_page: int, max_page_number: int):
    if current_page < max_page_number:
        st.session_state[ss.current_page] = current_page + 1


def decrement_page(current_page: int):
    if current_page > 1:
        st.session_state[ss.current_page] = current_page - 1


def display_page_content(image_files: list[str], current_page: int):
    with st.container(width=400, height=600):
        st.image(image_files[current_page - 1])


def display_navigation_controls(current_page: int, max_page_number: int):
    with st.container():
        left, center, right = st.columns(3)

        with left:
            st.button(label="前のページ", on_click=decrement_page, args=(current_page,), use_container_width=True)

        with center:
            st.write(f"ページ {current_page}/{max_page_number}")

        with right:
            st.button(
                label="次のページ",
                on_click=increment_page,
                args=(current_page, max_page_number),
                use_container_width=True,
            )


def display_chapter_management_sidebar(project: ProjectViewModel, selected_chapter_num: int):
    with st.sidebar:
        st.header("章管理")

        # Add new chapter button
        st.button("新しい章を追加", on_click=add_new_chapter, args=(project,), use_container_width=True)

        st.divider()

        # Display existing project
        if project:
            st.subheader("章一覧")
            for chapter_num in sorted(project.chapters.keys()):
                chapter_info = project.get_chapter_info(chapter_num)

                # Chapter selection and info
                is_selected = chapter_num == selected_chapter_num

                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        if st.button(
                            f"第{chapter_num}章",
                            key=f"select_chapter_{chapter_num}",
                            type="primary" if is_selected else "secondary",
                            use_container_width=True,
                        ):
                            select_chapter(chapter_num)
                            st.rerun()

                    with col2:
                        st.button(
                            "削除",
                            key=f"remove_chapter_{chapter_num}",
                            on_click=remove_chapter,
                            args=(chapter_num, project, selected_chapter_num),
                            use_container_width=True,
                        )

                    # Display chapter info
                    start_text = (
                        f"開始: P{chapter_info.start_page_number}"
                        if chapter_info.start_page_number > 0
                        else "開始: 未設定"
                    )
                    end_text = (
                        f"終了: P{chapter_info.end_page_number}" if chapter_info.end_page_number > 0 else "終了: 未設定"
                    )
                    st.caption(f"{start_text}")
                    st.caption(f"{end_text}")
        else:
            st.info("章が設定されていません。\n'新しい章を追加'ボタンで章を追加してください。")


def display_chapter_controls(selected_chapter_num: int, current_page: int, project: ProjectViewModel):
    if selected_chapter_num is None:
        st.info("章を選択してください")
        return

    st.subheader(f"第{selected_chapter_num}章の設定")

    chapter_info = project.get_chapter_info(selected_chapter_num)

    # Display current chapter info
    col1, col2 = st.columns(2)
    with col1:
        start_text = (
            f"開始ページ: P{chapter_info.start_page_number}"
            if chapter_info.start_page_number > 0
            else "開始ページ: 未設定"
        )
        st.info(start_text)
    with col2:
        end_text = (
            f"終了ページ: P{chapter_info.end_page_number}" if chapter_info.end_page_number > 0 else "終了ページ: 未設定"
        )
        st.info(end_text)

    st.divider()

    # Chapter setting buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            f"この章の開始ページに設定 (P{current_page})",
            on_click=set_chapter_start_page,
            args=(selected_chapter_num, current_page, project),
            use_container_width=True,
            type="primary",
        ):
            st.success(f"第{selected_chapter_num}章の開始ページをP{current_page}に設定しました")

    with col2:
        if st.button(
            f"この章の終了ページに設定 (P{current_page})",
            on_click=set_chapter_end_page,
            args=(selected_chapter_num, current_page, project),
            use_container_width=True,
            type="secondary",
        ):
            st.success(f"第{selected_chapter_num}章の終了ページをP{current_page}に設定しました")


def validate_and_proceed(project):
    st.divider()

    # Show summary
    with st.expander("章設定の確認", expanded=False):
        if project:
            summary = project.get_chapter_summary()
        else:
            summary = ""
        st.write(summary)

    if st.button("設定完了", type="primary", use_container_width=True):
        try:
            project.validate_chapter_config()
            logger.info("Chapter configuration validated successfully")
            st.switch_page(Rooter.podcast_page())
        except Exception as e:
            st.error(str(e))


def main():
    st.title("章設定")
    st.write("本のページを見ながら、各章の開始ページと終了ページを設定してください。")

    # Initialize session and get current state
    image_files, max_page_number, current_page, project, selected_chapter_num = initialize_session()

    # Initialize selected chapter if not set
    if selected_chapter_num is None and project.chapters:
        selected_chapter_num = min(project.chapters.keys())
        st.session_state[ss.selected_chapter_num] = selected_chapter_num

    # Display chapter management sidebar
    display_chapter_management_sidebar(project, selected_chapter_num)

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        # Display page content (image)
        display_page_content(image_files, current_page)

        # Display navigation controls
        display_navigation_controls(current_page, max_page_number)

    with col2:
        # Display chapter controls
        display_chapter_controls(selected_chapter_num, current_page, project)

        # Validate and proceed
        validate_and_proceed(project)


# Execute main function directly for Streamlit
main()
