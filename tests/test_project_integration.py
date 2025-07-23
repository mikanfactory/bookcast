"""
Integration tests for project processing with existing data.
"""

from bookcast.view_models import ChapterConfig, Chapters


def test_existing_project_status(service_manager, sample_filename):
    """Test existing project status check."""
    services = service_manager

    # Test with existing PDF
    result = services.file.get_project_status(sample_filename)

    assert result.success, f"Failed to get project status: {result.error}"

    status = result.data
    assert status["pdf_exists"], "PDF should exist"
    assert status["image_count"] > 0, "Should have processed images"
    assert status["text_count"] > 0, "Should have extracted text"


def test_file_content_access(service_manager, sample_filename):
    """Test accessing existing file content."""
    services = service_manager

    page_number = 1

    # Test text content access
    text_result = services.file.get_text_content(sample_filename, page_number)
    assert text_result.success, f"Failed to get text content: {text_result.error}"

    text_content = text_result.data
    assert len(text_content["content"]) > 0, "Text content should not be empty"
    assert text_content["page_number"] == page_number, "Page number should match"

    # Test image path access
    image_result = services.file.get_image_path(sample_filename, page_number)
    assert image_result.success, f"Failed to get image path: {image_result.error}"

    image_data = image_result.data
    assert image_data["page_number"] == page_number, "Page number should match"
    assert image_data["exists"], "Image should exist"


def test_chapter_service_with_mock_data(service_manager, sample_max_pages):
    """Test chapter service with mock chapter data."""
    services = service_manager

    # Create mock chapters like what would be created in the UI
    chapters = Chapters()
    chapters.chapters[1] = ChapterConfig(page_number=1)
    chapters.chapters[2] = ChapterConfig(page_number=10)
    chapters.specified_max_chapter = 2

    # Test validation
    validation_result = services.chapter.validate_chapter_config(chapters)
    assert validation_result.success, (
        f"Chapter validation failed: {validation_result.error}"
    )

    # Test page ranges calculation
    ranges_result = services.chapter.get_chapter_page_ranges(chapters, sample_max_pages)
    assert ranges_result.success, (
        f"Failed to calculate page ranges: {ranges_result.error}"
    )

    ranges = ranges_result.data
    assert len(ranges) == 2, "Should have 2 chapter ranges"
    assert ranges[0] == (1, 9), "Chapter 1 should be pages 1-9"
    assert ranges[1] == (10, sample_max_pages), (
        f"Chapter 2 should be pages 10-{sample_max_pages}"
    )


def test_list_available_projects(service_manager):
    """Test listing available projects."""
    services = service_manager

    result = services.file.list_available_projects()
    assert result.success, f"Failed to list projects: {result.error}"

    projects = result.data["projects"]
    assert isinstance(projects, list), "Projects should be a list"

    # Should find at least some existing PDF files (if any exist)
    # This test is more lenient as it depends on existing data
    for project in projects:
        assert "filename" in project, "Project should have filename"
        assert "status" in project, "Project should have status"

        status = project["status"]
        assert "pdf_exists" in status, "Status should include pdf_exists"
        assert "image_count" in status, "Status should include image_count"
        assert "text_count" in status, "Status should include text_count"


def test_chapter_page_ranges_edge_cases(service_manager):
    """Test chapter page ranges with edge cases."""
    services = service_manager

    # Test with single chapter
    chapters = Chapters()
    chapters.chapters[1] = ChapterConfig(page_number=1)
    chapters.specified_max_chapter = 1

    ranges_result = services.chapter.get_chapter_page_ranges(chapters, 10)
    assert ranges_result.success, "Should calculate ranges for single chapter"

    ranges = ranges_result.data
    assert len(ranges) == 1, "Should have 1 chapter range"
    assert ranges[0] == (1, 10), "Single chapter should span all pages"

    # Test with multiple chapters
    chapters.chapters[2] = ChapterConfig(page_number=5)
    chapters.chapters[3] = ChapterConfig(page_number=8)
    chapters.specified_max_chapter = 3

    ranges_result = services.chapter.get_chapter_page_ranges(chapters, 10)
    assert ranges_result.success, "Should calculate ranges for multiple chapters"

    ranges = ranges_result.data
    assert len(ranges) == 3, "Should have 3 chapter ranges"
    assert ranges[0] == (1, 4), "First chapter should be pages 1-4"
    assert ranges[1] == (5, 7), "Second chapter should be pages 5-7"
    assert ranges[2] == (8, 10), "Third chapter should be pages 8-10"


def test_file_service_error_handling(service_manager):
    """Test file service error handling with non-existent files."""
    services = service_manager

    # Test with non-existent file
    fake_filename = "non_existent_file.pdf"

    # Test project status for non-existent file
    result = services.file.get_project_status(fake_filename)
    assert result.success, "Should succeed even for non-existent files"

    status = result.data
    assert not status["pdf_exists"], "Non-existent PDF should be marked as not existing"

    # Test text content access for non-existent file
    text_result = services.file.get_text_content(fake_filename, 1)
    assert not text_result.success, "Should fail for non-existent text file"

    # Test image access for non-existent file
    image_result = services.file.get_image_path(fake_filename, 1)
    assert not image_result.success, "Should fail for non-existent image file"
