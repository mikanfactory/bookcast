from enum import StrEnum

import streamlit as st


class PageName(StrEnum):
    PROJECT = "project"
    CHAPTER = "chapter"
    PODCAST = "podcast"


class Rooter:
    RootMap = {
        PageName.PROJECT: "pages/project.py",
        PageName.CHAPTER: "pages/select_chapter.py",
        PageName.PODCAST: "pages/podcast.py",
    }

    @classmethod
    def project_page(cls):
        return cls.RootMap[PageName.PROJECT]

    @classmethod
    def chapter_page(cls):
        return cls.RootMap[PageName.CHAPTER]

    @classmethod
    def podcast_page(cls):
        return cls.RootMap[PageName.PODCAST]


def create_page():
    project_page = st.Page(
        Rooter.project_page(),
        title="プロジェクトの選択",
    )
    chapter_page = st.Page(
        Rooter.chapter_page(),
        title="章の選択",
    )
    podcast_page = st.Page(Rooter.podcast_page(), title="ポッドキャスト")

    pg = st.navigation(
        [
            project_page,
            chapter_page,
            podcast_page,
        ],
        # [chapter_page, podcast_setting_page, podcast_page],
        position="hidden",
    )
    st.set_page_config(page_title="Bookcast", layout="wide")
    pg.run()
