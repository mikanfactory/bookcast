import streamlit as st

from bookcast.page import Rooter
from bookcast.voice_option import VoiceOptions


def main():
    st.write("podcast setting page")
    voice_options = VoiceOptions()

    with st.form("podcast_setting_form"):
        num_of_people = st.selectbox("人数の選択", options=list(range(1, 3)))
        personality1 = st.selectbox(
            "話者1の性格を選択", options=voice_options.formatted_options, index=0
        )

        personality1_option = voice_options.resolve_voice_option_by_formatted_string(
            personality1
        )

        personality2 = st.selectbox(
            "話者2の性格を選択", options=voice_options.formatted_options, index=0
        )
        personality2_option = voice_options.resolve_voice_option_by_formatted_string(
            personality1
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

    with st.expander("話者の試聴", expanded=False):
        sample_voice_actor = st.selectbox(
            "話者の性格を選択", options=voice_options.formatted_options, index=0
        )
        sample_voice_actor_option = (
            voice_options.resolve_voice_option_by_formatted_string(sample_voice_actor)
        )
        st.audio(f"downloads/sample_voices/{sample_voice_actor_option.voice_name}.wav")


if __name__ == "__main__":
    main()
