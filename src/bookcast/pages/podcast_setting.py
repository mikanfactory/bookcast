import asyncio
import time

import streamlit as st
from streamlit.logger import get_logger

from bookcast.models import PodcastSetting
from bookcast.page import Rooter
from bookcast.services import get_service_manager
from bookcast.voice_option import VoiceOptions

logger = get_logger(__name__)


def initialize_session(services):
    """Initialize session state and validate required data."""
    # Ensure required session data exists
    filename = services.session.get_filename()
    max_page_number = services.session.get_max_page_number()
    chapters = services.session.get_chapters()

    if not filename or not max_page_number or not chapters.chapters:
        st.error(
            "必要なデータが不足しています。プロジェクトの選択と章の設定を完了してください。"
        )
        st.stop()

    return filename, max_page_number, chapters


def display_voice_selection(voice_options, num_of_people):
    """Display voice selection interface."""
    col1, col2 = st.columns(2)

    with col1:
        personality1 = st.selectbox(
            "話者1の性格を選択",
            options=voice_options.formatted_male_options
            + voice_options.formatted_female_options,
            index=10,
        )
        personality1_option = voice_options.resolve_voice_option(personality1)
        if personality1_option:
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
        if personality2_option:
            st.audio(
                f"downloads/sample_voices/{personality2_option.voice_name}.wav",
                end_time=0 if disabled else None,
            )

    return personality1_option, personality2_option


def validate_voice_selection(personality1_option, personality2_option, num_of_people):
    """Validate voice selection."""
    if not personality1_option:
        st.error("話者1の音声選択に問題があります。")
        return False

    if num_of_people >= 2 and not personality2_option:
        st.error("話者2の音声選択に問題があります。")
        return False

    return True


async def generate_podcast_script(
    services, filename, max_page_number, chapters, podcast_setting
):
    """Generate podcast script using service layer."""
    try:
        result = await services.podcast.generate_podcast_scripts(
            filename=filename,
            max_page_number=max_page_number,
            chapters=chapters,
            podcast_setting=podcast_setting,
        )

        if result.success:
            return result.data["combined_script"]
        else:
            st.error(f"スクリプト生成に失敗しました: {result.error}")
            return None

    except Exception as e:
        logger.error(f"Script generation failed: {str(e)}")
        st.error(f"スクリプト生成中にエラーが発生しました: {str(e)}")
        return None


def process_podcast_generation(
    services, filename, max_page_number, chapters, podcast_setting
):
    """Process podcast generation with proper error handling."""
    try:
        # Save podcast setting to session
        setting_result = services.session.set_podcast_setting(podcast_setting)
        if not setting_result.success:
            st.error(f"設定の保存に失敗しました: {setting_result.error}")
            return False

        with st.spinner("ポッドキャストの台本を生成中..."):
            # Generate script using async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                podcast_script = loop.run_until_complete(
                    generate_podcast_script(
                        services, filename, max_page_number, chapters, podcast_setting
                    )
                )
            finally:
                loop.close()

        if podcast_script:
            # Save script to session
            script_result = services.session.set_podcast_script(podcast_script)
            if script_result.success:
                st.success("台本の作成が完了しました！")
                logger.info("Successfully generated podcast script")
                return True
            else:
                st.error(f"スクリプトの保存に失敗しました: {script_result.error}")
                return False
        else:
            return False

    except Exception as e:
        logger.error(f"Podcast generation process failed: {str(e)}")
        st.error(f"台本生成処理中にエラーが発生しました: {str(e)}")
        return False


def main():
    """Main function for the podcast setting page."""
    st.write("podcast setting page")

    # Get service manager
    services = get_service_manager()

    # Initialize session and validate data
    filename, max_page_number, chapters = initialize_session(services)

    # Initialize voice options
    voice_options = VoiceOptions()

    # Number of people selection
    num_of_people = st.selectbox("人数の選択", options=list(range(1, 3)), index=1)

    # Voice selection
    personality1_option, personality2_option = display_voice_selection(
        voice_options, num_of_people
    )

    # Podcast length setting
    length_of_podcast = st.number_input(
        "ポッドキャストの長さ（分）",
        min_value=1,
        max_value=20,
        step=1,
        value=10,
    )

    # Custom prompt input
    prompt = st.text_area("台本作成用のプロンプト")

    # Generation button
    submitted = st.button("ポッドキャストを生成開始")
    if submitted:
        # Validate voice selection
        if not validate_voice_selection(
            personality1_option, personality2_option, num_of_people
        ):
            return

        # Create podcast setting
        podcast_setting = PodcastSetting(
            num_of_people=num_of_people,
            personality1_name=personality1_option.voice_name,
            personality2_name=personality2_option.voice_name
            if personality2_option
            else "",
            length=length_of_podcast,
            prompt=prompt,
        )

        # Process podcast generation
        if process_podcast_generation(
            services, filename, max_page_number, chapters, podcast_setting
        ):
            time.sleep(3)
            st.switch_page(Rooter.podcast_script_page())


# Execute main function directly for Streamlit
main()
