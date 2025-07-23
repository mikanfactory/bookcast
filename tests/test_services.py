"""
Tests for service layer functionality.
"""

from bookcast.view_models import ChapterConfig, Chapters


def test_service_manager_initialization(service_manager):
    """Test service manager initialization."""
    services = service_manager

    # Test that all services are available
    assert services.file is not None, "FileService should be available"
    assert services.pdf_processing is not None, (
        "PDFProcessingService should be available"
    )
    assert services.chapter is not None, "ChapterService should be available"
    assert services.podcast is not None, "PodcastService should be available"
    assert services.session is not None, "SessionService should be available"


def test_file_service_basic_functionality(service_manager):
    """Test file service basic functionality."""
    services = service_manager

    # Test project listing (should not fail even if empty)
    result = services.file.list_available_projects()
    assert result.success, f"Failed to list projects: {result.error}"


def test_chapter_service_validation(service_manager):
    """Test chapter service validation functionality."""
    services = service_manager

    # Test chapter validation with empty chapters
    chapters = Chapters()
    result = services.chapter.validate_chapter_config(chapters)
    assert not result.success, "Empty chapters should fail validation"

    # Test adding a chapter
    chapter_config = ChapterConfig(page_number=1)
    chapters.chapters[1] = chapter_config
    chapters.specified_max_chapter = 1

    result = services.chapter.validate_chapter_config(chapters)
    assert result.success, f"Valid chapters should pass validation: {result.error}"


def test_chapter_service_summary(service_manager):
    """Test chapter service summary functionality."""
    services = service_manager

    # Create a chapter for testing
    chapters = Chapters()
    chapter_config = ChapterConfig(page_number=1)
    chapters.chapters[1] = chapter_config
    chapters.specified_max_chapter = 1

    # Test chapter summary
    result = services.chapter.get_chapter_summary(chapters)
    assert result.success, f"Failed to get chapter summary: {result.error}"
    assert "第1章" in result.data, "Summary should contain chapter 1"


def test_podcast_service_initialization(service_manager):
    """Test podcast service initialization."""
    services = service_manager

    # Test that the service is properly initialized
    assert services.podcast.gemini_client is not None, (
        "Gemini client should be initialized"
    )
    assert services.podcast.script_model == "gemini-2.0-flash", (
        "Model should be set correctly"
    )


def test_session_service_structure(service_manager):
    """Test session service basic structure."""
    services = service_manager

    # Test that the service has expected methods
    assert hasattr(services.session, "get_chapters"), (
        "SessionService should have get_chapters method"
    )
    assert hasattr(services.session, "set_chapters"), (
        "SessionService should have set_chapters method"
    )
    assert hasattr(services.session, "get_filename"), (
        "SessionService should have get_filename method"
    )
    assert hasattr(services.session, "set_filename"), (
        "SessionService should have set_filename method"
    )


def test_chapter_service_add_chapter(service_manager):
    """Test adding chapters through chapter service."""
    services = service_manager

    chapters = Chapters()

    # Test adding a chapter
    result = services.chapter.add_chapter(chapters, 1, 5)
    assert result.success, f"Failed to add chapter: {result.error}"

    updated_chapters = result.data
    assert 1 in updated_chapters.chapters, "Chapter 1 should be added"
    assert updated_chapters.chapters[1].page_number == 5, (
        "Chapter 1 should start at page 5"
    )
    assert updated_chapters.specified_max_chapter == 1, "Max chapter should be 1"


def test_chapter_service_page_ranges(service_manager):
    """Test page ranges calculation."""
    services = service_manager

    chapters = Chapters()
    chapters.chapters[1] = ChapterConfig(page_number=1)
    chapters.chapters[2] = ChapterConfig(page_number=10)
    chapters.specified_max_chapter = 2

    # Test page ranges calculation
    result = services.chapter.get_chapter_page_ranges(chapters, 20)
    assert result.success, f"Failed to calculate page ranges: {result.error}"

    ranges = result.data
    assert len(ranges) == 2, "Should have 2 chapter ranges"
    assert ranges[0] == (1, 9), "Chapter 1 should be pages 1-9"
    assert ranges[1] == (10, 20), "Chapter 2 should be pages 10-20"
