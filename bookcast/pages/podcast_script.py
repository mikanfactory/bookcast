import streamlit as st
from bookcast.session_state import SessionState as State

st.write("podcast script page")

podcast_script = st.session_state[State.podcast_script]
st.write(podcast_script)
