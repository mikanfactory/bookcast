import time
import streamlit as st

from bookcast.page import Rooter
from bookcast.script_writing import generate_script
from bookcast.voice_option import VoiceOptions
from bookcast.models import PodcastSetting
from bookcast.session_state import SessionState as State


def main():
    st.write("podcast setting page")
    voice_options = VoiceOptions()

    num_of_people = st.selectbox("人数の選択", options=list(range(1, 3)), index=1)

    col1, col2 = st.columns(2)
    with col1:
        personality1 = st.selectbox(
            "話者1の性格を選択",
            options=voice_options.formatted_male_options
            + voice_options.formatted_female_options,
            index=10,
        )
        personality1_option = voice_options.resolve_voice_option(personality1)
        st.audio(f"downloads/sample_voices/{personality1_option.voice_name}.wav")

    with col2:
        disabled = num_of_people == 1
        personality2 = st.selectbox(
            "話者2の性格を選択",
            options=voice_options.formatted_female_options
            + voice_options.formatted_male_options,
            index=6,
            disabled=disabled,
        )
        personality2_option = voice_options.resolve_voice_option(personality2)
        st.audio(
            f"downloads/sample_voices/{personality2_option.voice_name}.wav",
            end_time=0 if disabled else None,
        )

    length_of_podcast = st.number_input(
        "ポッドキャストの長さ（分）",
        min_value=1,
        max_value=20,
        step=1,
        value=10,
    )

    prompt = st.text_area("台本作成用のプロンプト")

    submitted = st.button("ポッドキャストを生成開始")
    if submitted:
        podcast_setting = PodcastSetting(
            num_of_people=num_of_people,
            personality1_name=personality1_option.voice_name,
            personality2_name=personality2_option.voice_name,
            length=length_of_podcast,
            prompt=prompt,
        )
        st.session_state.podcast_setting = podcast_setting

        with st.spinner("ポッドキャストの台本を生成中..."):
            podcast_script = generate_script(
                filename=st.session_state[State.filename],
                max_page_number=st.session_state[State.max_page_number],
                chapters=st.session_state[State.chapters],
                podcast_setting=podcast_setting,
            )

        st.success(f"台本の作成が完了しました！")
        st.session_state[State.podcast_script] = podcast_script

        time.sleep(3)
        st.switch_page(Rooter.podcast_script_page())


if __name__ == "__main__":
    main()
