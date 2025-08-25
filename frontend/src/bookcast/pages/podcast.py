import requests
import streamlit as st
from streamlit.logger import get_logger

from bookcast.config import BACKEND_URL
from bookcast.session_state import SessionState as ss
from bookcast.view_models import ProjectViewModel

logger = get_logger(__name__)


def fetch_project_status(project: ProjectViewModel) -> str:
    url = f"{BACKEND_URL}/api/v1/projects/{project.project_id}"
    resp = requests.get(url)
    if resp.ok:
        project = resp.json()
        status = project["status"]
    else:
        st.error("Failed to fetch project status. Please try again later.")
        raise ConnectionError

    return status


def download_audio_file(project: ProjectViewModel) -> str:
    url = f"{BACKEND_URL}/api/v1/projects/{project.project_id}/download"
    resp = requests.get(url)
    if resp.ok:
        path = f"downloads/project_{project.project_id}.zip"
        with open(path, "wb") as file:
            file.write(resp.content)
        logger.info(f"Downloaded completed audio to {path}")
        return path
    else:
        logger.error(f"Failed to download completed audio for project {project.project_id}.")
        logger.error(resp.text)
        st.error("Failed to download audio file. Please try again later.")
        raise ConnectionError


def add_download_button(project: ProjectViewModel, downloaded_path: str | None):
    if not downloaded_path:
        with st.spinner("音声ファイルをダウンロードしています..."):
            path = download_audio_file(project)
            st.session_state[ss.downloaed_path] = path

    with open(downloaded_path, "rb") as file:
        st.download_button("Download Audio", data=file.read(), file_name="audio.zip")


def main():
    st.write("podcast page")
    project = st.session_state.get(ss.project)
    downloaded_path = st.session_state.get(ss.downloaed_path)

    status = fetch_project_status(project)
    match status:
        case "not_started":
            st.write("プロジェクトはまだ開始されていません。")
        case "start_ocr":
            st.write("OCR処理を開始しています。")
        case "ocr_completed":
            st.write("OCR処理が完了しました。次はスクリプトの作成です。")
        case "start_writing_script":
            st.write("スクリプトの作成を開始しています。")
        case "writing_script_completed":
            st.write("スクリプトの作成が完了しました。次はTTS処理です。")
        case "start_tts":
            st.write("TTS処理を開始しています。")
        case "tts_completed":
            st.write("TTS処理が完了しました。次は音声の作成です。")
        case "start_creating_audio":
            st.write("音声の作成を開始してください。")
        case "creating_audio_completed":
            st.write("音声の作成が完了しました！")
            add_download_button(project, downloaded_path)


# Execute main function directly for Streamlit
main()
