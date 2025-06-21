import streamlit as st


def create_page():
    project_page = st.Page(
        "bookcast/pages/project.py", title="プロジェクトの選択", icon=":material/add_circle:"
    )
    chapter_page = st.Page(
        "bookcast/pages/select_chapter.py", title="章の選択", icon=":material/add_circle:"
    )
    podcast_setting_page = st.Page(
        "bookcast/pages/podcast_setting.py", title="ポッドキャストの設定", icon=":material/delete:"
    )
    podcast_page = st.Page(
        "bookcast/pages/podcast.py", title="ポッドキャスト", icon=":material/delete:"
    )

    pg = st.navigation(
        [project_page, chapter_page, podcast_setting_page, podcast_page], position="hidden"
    )
    st.set_page_config(page_title="Data manager", page_icon=":material/edit:")
    pg.run()
