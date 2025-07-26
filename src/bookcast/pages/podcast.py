import streamlit as st
from streamlit.logger import get_logger

from bookcast.services import get_service_manager

logger = get_logger(__name__)


def display_podcast_info(services):
    """Display podcast generation information and final output."""
    st.markdown("### ポッドキャスト生成完了")

    # Get session summary
    summary_result = services.session.get_session_summary()

    if summary_result.success:
        summary = summary_result.data

        # Display project info
        st.markdown("#### プロジェクト情報")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**ファイル名**: {summary.get('filename', 'N/A')}")
            chapters = summary.get("chapters", {})
            if hasattr(chapters, "chapters"):
                st.write(f"**章数**: {len(chapters.chapters)}")
            else:
                st.write("**章数**: 0")

        with col2:
            st.write(f"**最大ページ数**: {summary.get('max_page_number', 'N/A')}")
            st.write(f"**台本生成済み**: {'はい' if summary.get('has_podcast_script') else 'いいえ'}")

        # Display podcast settings
        podcast_setting = summary.get("podcast_setting")
        if podcast_setting:
            st.markdown("#### ポッドキャスト設定")
            st.write(f"**話者数**: {podcast_setting.num_of_people}人")
            st.write(f"**話者1**: {podcast_setting.personality1_name}")
            if podcast_setting.num_of_people >= 2:
                st.write(f"**話者2**: {podcast_setting.personality2_name}")
            st.write(f"**長さ**: {podcast_setting.length}分")

            if podcast_setting.prompt:
                with st.expander("カスタムプロンプト"):
                    st.write(podcast_setting.prompt)

        # Display script preview if available
        podcast_script = services.session.get_podcast_script()
        if podcast_script:
            st.markdown("#### 台本プレビュー")
            with st.expander("台本を表示"):
                st.text(podcast_script[:1000] + "..." if len(podcast_script) > 1000 else podcast_script)

            # Download button
            st.download_button(
                label="📄 完成した台本をダウンロード",
                data=podcast_script,
                file_name=f"{summary.get('filename', 'podcast')}_script.txt",
                mime="text/plain",
                type="primary",
            )
        else:
            st.warning("台本が生成されていません。")

    else:
        st.error(f"セッション情報の取得に失敗しました: {summary_result.error}")


def display_next_steps():
    """Display next steps and options."""
    st.markdown("#### 次のステップ")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 新しいプロジェクトを開始", type="secondary"):
            # Clear session state for new project
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

    with col2:
        st.markdown("**今後の機能追加予定:**")
        st.markdown("- 🎵 音声合成機能")
        st.markdown("- 🎧 音声プレビュー")
        st.markdown("- 📤 ポッドキャスト配信")


def main():
    """Main function for the podcast page."""
    st.write("podcast page")

    # Get service manager
    services = get_service_manager()

    # Display podcast info
    display_podcast_info(services)

    # Display next steps
    display_next_steps()

    logger.info("Displayed podcast completion page")


# Execute main function directly for Streamlit
main()
