import streamlit as st
from streamlit.logger import get_logger

from bookcast.services import get_service_manager

logger = get_logger(__name__)


def display_script_content(services):
    """Display the generated podcast script."""
    podcast_script = services.session.get_podcast_script()

    if podcast_script:
        st.markdown("### 生成されたポッドキャスト台本")

        # Display script in a scrollable container
        with st.container(height=600):
            st.markdown(podcast_script)

        # Download button for the script
        st.download_button(
            label="台本をダウンロード",
            data=podcast_script,
            file_name="podcast_script.txt",
            mime="text/plain",
        )

        logger.info("Successfully displayed podcast script")
    else:
        st.error("台本が見つかりません。ポッドキャスト設定画面に戻って台本を生成してください。")
        logger.warning("No podcast script found in session")


def display_session_info(services):
    """Display current session information."""
    with st.expander("セッション情報", expanded=False):
        summary_result = services.session.get_session_summary()

        if summary_result.success:
            summary = summary_result.data
            st.write(f"**ファイル名**: {summary.get('filename', 'N/A')}")
            st.write(f"**章数**: {len(summary.get('chapters', {}).chapters) if summary.get('chapters') else 0}")

            podcast_setting = summary.get("podcast_setting")
            if podcast_setting:
                st.write(f"**話者数**: {podcast_setting.num_of_people}")
                st.write(f"**長さ**: {podcast_setting.length}分")
                if podcast_setting.prompt:
                    st.write(f"**カスタムプロンプト**: {podcast_setting.prompt[:100]}...")
        else:
            st.error(f"セッション情報の取得に失敗しました: {summary_result.error}")


def main():
    """Main function for the podcast script page."""
    st.write("podcast script page")

    # Get service manager
    services = get_service_manager()

    # Display script content
    display_script_content(services)

    # Display session information
    display_session_info(services)


# Execute main function directly for Streamlit
main()
