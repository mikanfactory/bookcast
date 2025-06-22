import streamlit as st
from bookcast.voice_option import voice_options

st.write("podcast page")

voice_names = [voice.voice_name for voice in voice_options.options]
selected_voice_name = st.selectbox(
    "音声オプションの選択",
    options=voice_names,
    label_visibility="hidden",
    index=0,
    placeholder="音声オプションを選択してください",
)

if selected_voice_name:
    description = [voice.description for voice in voice_options.options if voice.voice_name == selected_voice_name]
    st.write(description)


st.audio(f"downloads/sample_voices/{selected_voice_name}.wav")
