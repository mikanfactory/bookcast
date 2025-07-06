"""
Tests for the refactored select_chapter functionality.
"""

from bookcast.models import ChapterConfig, Chapters


class TestSelectChapterPage:
    """Test class for select_chapter page functionality."""

    def test_session_initialization(
        self, service_manager, sample_filename, sample_max_pages
    ):
        """Test session initialization for select_chapter page."""
        services = service_manager

        # Test session initialization (simulate what happens in select_chapter)
        current_page = 1

        # Set initial session values
        services.session.set_filename(sample_filename)
        services.session.set_max_page_number(sample_max_pages)
        services.session.set_current_page(current_page)

        # Initialize chapters
        chapters = Chapters()
        services.session.set_chapters(chapters)

        # Verify session state
        assert services.session.get_filename() == sample_filename
        assert services.session.get_max_page_number() == sample_max_pages
        assert services.session.get_current_page() == current_page

    def test_page_content_access(self, service_manager, sample_filename):
        """Test page content access functionality."""
        services = service_manager
        current_page = 1

        # Test image access
        image_result = services.file.get_image_path(sample_filename, current_page)
        assert image_result.success, f"Failed to get image: {image_result.error}"
        assert image_result.data["page_number"] == current_page

        # Test text access
        text_result = services.file.get_text_content(sample_filename, current_page)
        assert text_result.success, f"Failed to get text: {text_result.error}"
        assert len(text_result.data["content"]) > 0, "Text content should not be empty"

    def test_chapter_management(self, service_manager):
        """Test chapter addition and management functionality."""
        services = service_manager

        # Start with empty chapters
        chapters = Chapters()

        # Test adding chapters (simulating user interaction)
        chapter_additions = [
            (1, 1),  # Chapter 1 starts at page 1
            (2, 10),  # Chapter 2 starts at page 10
        ]

        for chapter_num, page_num in chapter_additions:
            result = services.chapter.add_chapter(chapters, chapter_num, page_num)
            assert result.success, (
                f"Failed to add chapter {chapter_num}: {result.error}"
            )
            chapters = result.data

        # Test chapter summary
        summary_result = services.chapter.get_chapter_summary(chapters)
        assert summary_result.success, f"Failed to get summary: {summary_result.error}"
        assert "第1章" in summary_result.data
        assert "第2章" in summary_result.data

        # Test chapter validation
        validation_result = services.chapter.validate_chapter_config(chapters)
        assert validation_result.success, (
            f"Chapter validation failed: {validation_result.error}"
        )

        # Test page ranges calculation
        ranges_result = services.chapter.get_chapter_page_ranges(chapters, 23)
        assert ranges_result.success, (
            f"Failed to calculate ranges: {ranges_result.error}"
        )
        ranges = ranges_result.data
        assert len(ranges) == 2
        assert ranges[0] == (1, 9)
        assert ranges[1] == (10, 23)

    def test_navigation_functionality(self, service_manager):
        """Test page navigation functionality."""
        services = service_manager

        # Initialize session
        services.session.set_current_page(5)
        services.session.set_max_page_number(23)

        current_page = services.session.get_current_page()
        max_page_number = services.session.get_max_page_number()

        assert current_page == 5, "Current page should be 5"
        assert max_page_number == 23, "Max page should be 23"

        # Test increment (next page)
        if current_page < max_page_number:
            services.session.set_current_page(current_page + 1)
            new_page = services.session.get_current_page()
            assert new_page == 6, "Page should increment to 6"

        # Test decrement (previous page)
        current_page = services.session.get_current_page()
        if current_page > 1:
            services.session.set_current_page(current_page - 1)
            new_page = services.session.get_current_page()
            assert new_page == 5, "Page should decrement to 5"

    def test_session_consistency(
        self, service_manager, sample_filename, sample_max_pages
    ):
        """Test session state consistency."""
        services = service_manager

        # Set up complete session
        current_page = 1

        services.session.set_filename(sample_filename)
        services.session.set_max_page_number(sample_max_pages)
        services.session.set_current_page(current_page)

        chapters = Chapters()
        chapters.chapters[1] = ChapterConfig(page_number=1)
        chapters.specified_max_chapter = 1
        services.session.set_chapters(chapters)

        # Test session summary
        summary_result = services.session.get_session_summary()
        assert summary_result.success, (
            f"Failed to get session summary: {summary_result.error}"
        )

        summary = summary_result.data
        assert summary["filename"] == sample_filename
        assert summary["current_page"] == current_page
        assert summary["max_page_number"] == sample_max_pages
        assert len(summary["chapters"].chapters) == 1

        # Validate session
        validation_result = services.session.validate_session_state()
        assert validation_result.success, (
            f"Session validation failed: {validation_result.error}"
        )


class TestChapterManagementEdgeCases:
    """Test edge cases for chapter management."""

    def test_empty_chapter_validation(self, service_manager):
        """Test validation of empty chapters."""
        services = service_manager

        chapters = Chapters()
        result = services.chapter.validate_chapter_config(chapters)
        assert not result.success, "Empty chapters should fail validation"

    def test_duplicate_page_validation(self, service_manager):
        """Test validation with duplicate page numbers."""
        services = service_manager

        chapters = Chapters()
        # Add chapters with duplicate page numbers
        chapters.chapters[1] = ChapterConfig(page_number=5)
        chapters.chapters[2] = ChapterConfig(page_number=5)  # Duplicate!
        chapters.specified_max_chapter = 2

        result = services.chapter.validate_chapter_config(chapters)
        assert not result.success, "Duplicate page numbers should fail validation"
        assert "重複" in result.error, "Error message should mention duplicates"

    def test_incomplete_chapter_sequence(self, service_manager):
        """Test validation with incomplete chapter sequence."""
        services = service_manager

        chapters = Chapters()
        chapters.chapters[1] = ChapterConfig(page_number=1)
        chapters.chapters[3] = ChapterConfig(page_number=10)  # Missing chapter 2!
        chapters.specified_max_chapter = 3

        result = services.chapter.validate_chapter_config(chapters)
        assert not result.success, "Incomplete chapter sequence should fail validation"
        assert "不完全" in result.error, (
            "Error message should mention incomplete chapters"
        )

    def test_single_chapter_page_ranges(self, service_manager):
        """Test page ranges with a single chapter."""
        services = service_manager

        chapters = Chapters()
        chapters.chapters[1] = ChapterConfig(page_number=1)
        chapters.specified_max_chapter = 1

        result = services.chapter.get_chapter_page_ranges(chapters, 20)
        assert result.success, "Should calculate ranges for single chapter"

        ranges = result.data
        assert len(ranges) == 1
        assert ranges[0] == (1, 20), "Single chapter should span all pages"

    def test_chapter_removal(self, service_manager):
        """Test chapter removal functionality."""
        services = service_manager

        chapters = Chapters()
        chapters.chapters[1] = ChapterConfig(page_number=1)
        chapters.chapters[2] = ChapterConfig(page_number=10)
        chapters.specified_max_chapter = 2

        # Remove chapter 2
        result = services.chapter.remove_chapter(chapters, 2)
        assert result.success, "Should be able to remove chapter"

        updated_chapters = result.data
        assert 2 not in updated_chapters.chapters, "Chapter 2 should be removed"
        assert updated_chapters.specified_max_chapter == 1, (
            "Max chapter should be updated"
        )
