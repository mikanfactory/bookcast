import streamlit as st

from enum import StrEnum


class PageName(StrEnum):
    PROJECT = "project"
    CHAPTER = "chapter"
    PODCAST_SETTING = "podcast_setting"
    PODCAST = "podcast"


class Rooter:
    RootMap = {
        PageName.PROJECT: "bookcast/pages/project.py",
        PageName.CHAPTER: "bookcast/pages/select_chapter.py",
        PageName.PODCAST_SETTING: "bookcast/pages/podcast_setting.py",
        PageName.PODCAST: "bookcast/pages/podcast.py",
    }

    @classmethod
    def project_page(cls):
        return cls.RootMap[PageName.PROJECT]

    @classmethod
    def chapter_page(cls):
        return cls.RootMap[PageName.CHAPTER]

    @classmethod
    def podcast_setting_page(cls):
        return cls.RootMap[PageName.PODCAST_SETTING]

    @classmethod
    def podcast_page(cls):
        return cls.RootMap[PageName.PODCAST]


def create_page():
    project_page = st.Page(
        "bookcast/pages/project.py",
        title="プロジェクトの選択",
        icon=":material/add_circle:",
    )
    chapter_page = st.Page(
        "bookcast/pages/select_chapter.py",
        title="章の選択",
        icon=":material/add_circle:",
    )
    podcast_setting_page = st.Page(
        "bookcast/pages/podcast_setting.py",
        title="ポッドキャストの設定",
        icon=":material/delete:",
    )
    podcast_page = st.Page(
        "bookcast/pages/podcast.py", title="ポッドキャスト", icon=":material/delete:"
    )

    pg = st.navigation(
        [project_page, chapter_page, podcast_setting_page, podcast_page],
        # [chapter_page, podcast_setting_page, podcast_page],
        position="hidden",
    )
    st.set_page_config(page_title="Bookcast", layout="wide")
    pg.run()
