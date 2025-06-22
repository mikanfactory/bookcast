import streamlit as st

from bookcast.page import Rooter


def main():
    st.write("podcast setting page")

    with st.form("podcast_setting_form"):
        num_of_people = st.selectbox("人数の選択", options=list(range(1, 3)))
        personality1 = st.selectbox(
            "話者1の性格を選択", options=["元気", "落ち着き", "クール"]
        )
        personality2 = st.selectbox(
            "話者2の性格を選択", options=["元気", "落ち着き", "クール"]
        )
        length_of_podcast = st.number_input(
            "ポッドキャストの長さ（分）",
            min_value=1,
            max_value=15,
            step=1,
        )
        prompt = st.text_area("台本作成用のプロンプト")

        submitted = st.form_submit_button("ポッドキャストを生成開始")
        if submitted:
            st.switch_page(Rooter.podcast_page())


if __name__ == "__main__":
    main()
