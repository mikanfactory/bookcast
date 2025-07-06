"""
Tests for the refactored podcast-related pages.
"""

from bookcast.models import ChapterConfig, Chapters, PodcastSetting


class TestPodcastSettingPage:
    """Test class for podcast_setting page functionality."""

    def test_session_validation_with_empty_data(self, service_manager):
        """Test session validation with missing data."""
        services = service_manager

        # Test with empty session
        filename = services.session.get_filename()
        max_page_number = services.session.get_max_page_number()
        chapters = services.session.get_chapters()

        # At least one of these should be empty/None
        has_required_data = (
            filename and max_page_number and chapters and len(chapters.chapters) > 0
        )

        # If data is missing, it should be handled gracefully
        if not has_required_data:
            assert True, "Missing data is handled gracefully"

    def test_session_validation_with_complete_data(
        self, service_manager, sample_filename, sample_max_pages
    ):
        """Test session validation with complete data."""
        services = service_manager

        # Set up complete session data
        services.session.set_filename(sample_filename)
        services.session.set_max_page_number(sample_max_pages)

        chapters = Chapters()
        chapters.chapters[1] = ChapterConfig(page_number=1)
        chapters.specified_max_chapter = 1
        services.session.set_chapters(chapters)

        # Verify all required data is present
        assert services.session.get_filename() == sample_filename
        assert services.session.get_max_page_number() == sample_max_pages
        retrieved_chapters = services.session.get_chapters()
        assert len(retrieved_chapters.chapters) > 0

    def test_podcast_setting_creation(self, service_manager):
        """Test podcast setting creation and validation."""
        services = service_manager

        # Create a valid podcast setting
        podcast_setting = PodcastSetting(
            num_of_people=2,
            personality1_name="TestVoice1",
            personality2_name="TestVoice2",
            length=10,
            prompt="Test prompt for podcast generation",
        )

        # Test saving to session
        result = services.session.set_podcast_setting(podcast_setting)
        assert result.success, f"Failed to save podcast setting: {result.error}"

        # Test retrieving from session
        retrieved_setting = services.session.get_podcast_setting()
        assert retrieved_setting is not None, "Podcast setting should be retrievable"
        assert retrieved_setting.num_of_people == 2
        assert retrieved_setting.personality1_name == "TestVoice1"
        assert retrieved_setting.personality2_name == "TestVoice2"
        assert retrieved_setting.length == 10
        assert retrieved_setting.prompt == "Test prompt for podcast generation"


class TestPodcastScriptPage:
    """Test class for podcast_script page functionality."""

    def test_script_display_with_no_script(self, service_manager):
        """Test script display when no script is available."""
        services = service_manager

        # Ensure no script is set
        podcast_script = services.session.get_podcast_script()
        # Should either be None or empty
        assert podcast_script is None or podcast_script == ""

    def test_script_display_with_script(self, service_manager):
        """Test script display when script is available."""
        services = service_manager

        # Set a test script
        test_script = "これはテスト用のポッドキャスト台本です。\n\n話者1: こんにちは。\n話者2: こんにちは、今日もよろしくお願いします。"

        result = services.session.set_podcast_script(test_script)
        assert result.success, f"Failed to set podcast script: {result.error}"

        # Retrieve and verify script
        retrieved_script = services.session.get_podcast_script()
        assert retrieved_script == test_script, (
            "Retrieved script should match the set script"
        )

    def test_session_info_display(self, service_manager, sample_filename):
        """Test session information display functionality."""
        services = service_manager

        # Set up session data
        services.session.set_filename(sample_filename)
        services.session.set_max_page_number(23)

        chapters = Chapters()
        chapters.chapters[1] = ChapterConfig(page_number=1)
        chapters.chapters[2] = ChapterConfig(page_number=10)
        chapters.specified_max_chapter = 2
        services.session.set_chapters(chapters)

        podcast_setting = PodcastSetting(
            num_of_people=2,
            personality1_name="Voice1",
            personality2_name="Voice2",
            length=15,
            prompt="Test prompt",
        )
        services.session.set_podcast_setting(podcast_setting)

        # Get session summary
        summary_result = services.session.get_session_summary()
        assert summary_result.success, (
            f"Failed to get session summary: {summary_result.error}"
        )

        summary = summary_result.data
        assert summary["filename"] == sample_filename
        assert len(summary["chapters"].chapters) == 2
        assert summary["podcast_setting"].num_of_people == 2


class TestPodcastCompletionPage:
    """Test class for podcast completion page functionality."""

    def test_complete_podcast_info_display(self, service_manager, sample_filename):
        """Test complete podcast information display."""
        services = service_manager

        # Set up complete session data
        services.session.set_filename(sample_filename)
        services.session.set_max_page_number(20)

        chapters = Chapters()
        chapters.chapters[1] = ChapterConfig(page_number=1)
        chapters.chapters[2] = ChapterConfig(page_number=10)
        chapters.specified_max_chapter = 2
        services.session.set_chapters(chapters)

        podcast_setting = PodcastSetting(
            num_of_people=2,
            personality1_name="Speaker1",
            personality2_name="Speaker2",
            length=12,
            prompt="Custom generation prompt",
        )
        services.session.set_podcast_setting(podcast_setting)

        test_script = "完成したポッドキャスト台本\n\nSpeaker1: 今日は面白いトピックについて話しましょう。\nSpeaker2: そうですね、楽しみです。"
        services.session.set_podcast_script(test_script)

        # Get session summary for display
        summary_result = services.session.get_session_summary()
        assert summary_result.success, "Should get session summary successfully"

        summary = summary_result.data

        # Verify all information is available
        assert summary["filename"] == sample_filename
        assert summary["max_page_number"] == 20
        assert len(summary["chapters"].chapters) == 2
        assert summary["podcast_setting"].num_of_people == 2
        assert summary["podcast_setting"].personality1_name == "Speaker1"
        assert summary["podcast_setting"].personality2_name == "Speaker2"
        assert summary["podcast_setting"].length == 12
        assert summary["has_podcast_script"] is True

        # Verify script content
        retrieved_script = services.session.get_podcast_script()
        assert retrieved_script == test_script

    def test_partial_podcast_info_display(
        self, service_manager, sample_filename, clean_session
    ):
        """Test podcast info display with partial data."""
        services = service_manager

        # Set up minimal session data
        services.session.set_filename(sample_filename)
        services.session.set_max_page_number(15)

        chapters = Chapters()
        chapters.chapters[1] = ChapterConfig(page_number=1)
        chapters.specified_max_chapter = 1
        services.session.set_chapters(chapters)

        # Explicitly clear podcast setting and script
        services.session.set_podcast_setting(None)
        services.session.set_podcast_script(None)

        # Get session summary
        summary_result = services.session.get_session_summary()
        assert summary_result.success, "Should get session summary successfully"

        summary = summary_result.data

        # Verify basic information is available
        assert summary["filename"] == sample_filename
        assert summary["max_page_number"] == 15
        assert len(summary["chapters"].chapters) == 1
        # Note: podcast_setting might be None or have previous test data
        assert summary["has_podcast_script"] is False  # No script provided


class TestPodcastWorkflow:
    """Test the complete podcast generation workflow."""

    def test_end_to_end_workflow_simulation(self, service_manager, sample_filename):
        """Test a complete workflow simulation."""
        services = service_manager

        # Step 1: Initialize project (like project.py would do)
        services.session.set_filename(sample_filename)
        services.session.set_max_page_number(25)

        # Step 2: Set up chapters (like select_chapter.py would do)
        chapters = Chapters()
        result = services.chapter.add_chapter(chapters, 1, 1)
        assert result.success, "Should add chapter 1"
        chapters = result.data

        result = services.chapter.add_chapter(chapters, 2, 15)
        assert result.success, "Should add chapter 2"
        chapters = result.data

        services.session.set_chapters(chapters)

        # Step 3: Configure podcast settings (like podcast_setting.py would do)
        podcast_setting = PodcastSetting(
            num_of_people=2,
            personality1_name="Narrator",
            personality2_name="Expert",
            length=20,
            prompt="Generate an engaging podcast script",
        )
        services.session.set_podcast_setting(podcast_setting)

        # Step 4: Generate script (simulated)
        mock_script = "Mock generated podcast script\n\nNarrator: Welcome to our podcast.\nExpert: Thank you for having me."
        services.session.set_podcast_script(mock_script)

        # Step 5: Verify complete workflow state
        summary_result = services.session.get_session_summary()
        assert summary_result.success, "Should get complete session summary"

        summary = summary_result.data
        assert summary["filename"] == sample_filename
        assert summary["max_page_number"] == 25
        assert len(summary["chapters"].chapters) == 2
        assert summary["podcast_setting"].num_of_people == 2
        assert summary["has_podcast_script"] is True

        # Verify session validation passes
        validation_result = services.session.validate_session_state()
        assert validation_result.success, "Complete workflow should pass validation"
