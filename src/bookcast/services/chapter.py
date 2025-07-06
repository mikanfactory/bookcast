"""
Chapter management service for handling chapter selection and validation.
"""

from bookcast.models import ChapterConfig, Chapters
from bookcast.path_resolver import resolve_image_path, resolve_text_path
from bookcast.services.base import BaseService, ServiceResult


class ChapterService(BaseService):
    """Service for managing chapter selection and validation."""

    def validate_chapter_config(self, chapters: Chapters) -> ServiceResult:
        """
        Validate chapter configuration for completeness and consistency.

        Args:
            chapters: Chapters object to validate

        Returns:
            ServiceResult with validation results
        """
        try:
            self._log_info("Validating chapter configuration")

            specified_max_chapter = chapters.specified_max_chapter

            # Check if any chapters are selected
            if not chapters.chapters:
                return ServiceResult.failure(
                    "章が選択されていません。1つ以上選択してください。"
                )

            # Check if all chapters up to max are configured
            if len(chapters.chapters) < specified_max_chapter:
                missing_chapters = []
                expected = range(1, specified_max_chapter + 1)
                actual = chapters.chapters.keys()

                for chapter_num in expected:
                    if chapter_num not in actual:
                        missing_chapters.append(chapter_num)

                error_msg = (
                    "章の設定が不完全です。すべての章を設定してください。\n\n"
                    f"設定されていない章: {', '.join(map(str, missing_chapters))}"
                )
                return ServiceResult.failure(error_msg)

            # Check for duplicate page numbers
            specified_pages = set()
            duplicates = []

            for chapter_num, config in chapters.chapters.items():
                if config.page_number in specified_pages:
                    duplicates.append(config.page_number)
                else:
                    specified_pages.add(config.page_number)

            if duplicates:
                error_msg = (
                    "ページ番号の重複があります。以下のページ番号が重複しています:\n\n"
                    f"{', '.join(map(str, duplicates))}"
                )
                return ServiceResult.failure(error_msg)

            self._log_info("Chapter configuration is valid")
            return ServiceResult.success(
                {"valid": True, "chapters_count": len(chapters.chapters)}
            )

        except Exception as e:
            error_msg = f"Failed to validate chapter configuration: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def add_chapter(
        self, chapters: Chapters, chapter_num: int, page_number: int
    ) -> ServiceResult:
        """
        Add a new chapter configuration.

        Args:
            chapters: Chapters object to modify
            chapter_num: Chapter number
            page_number: Page number for the chapter

        Returns:
            ServiceResult with updated chapters
        """
        try:
            self._log_info(f"Adding chapter {chapter_num} at page {page_number}")

            config = ChapterConfig(page_number=page_number)
            chapters.chapters[chapter_num] = config
            chapters.specified_max_chapter = max(
                chapters.specified_max_chapter, chapter_num
            )

            self._log_info(f"Successfully added chapter {chapter_num}")
            return ServiceResult.success(chapters)

        except Exception as e:
            error_msg = f"Failed to add chapter: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def remove_chapter(self, chapters: Chapters, chapter_num: int) -> ServiceResult:
        """
        Remove a chapter configuration.

        Args:
            chapters: Chapters object to modify
            chapter_num: Chapter number to remove

        Returns:
            ServiceResult with updated chapters
        """
        try:
            self._log_info(f"Removing chapter {chapter_num}")

            if chapter_num not in chapters.chapters:
                return ServiceResult.failure(f"Chapter {chapter_num} not found")

            del chapters.chapters[chapter_num]

            # Update max chapter if necessary
            if chapters.chapters:
                chapters.specified_max_chapter = max(chapters.chapters.keys())
            else:
                chapters.specified_max_chapter = 1

            self._log_info(f"Successfully removed chapter {chapter_num}")
            return ServiceResult.success(chapters)

        except Exception as e:
            error_msg = f"Failed to remove chapter: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def get_chapter_summary(self, chapters: Chapters) -> ServiceResult:
        """
        Get a formatted summary of chapter configurations.

        Args:
            chapters: Chapters object

        Returns:
            ServiceResult with formatted summary string
        """
        try:
            if not chapters.chapters:
                return ServiceResult.success("設定された章はありません。")

            summary_lines = []
            for chapter_num, config in sorted(chapters.chapters.items()):
                summary_lines.append(f"第{chapter_num}章: ページ {config.page_number}")

            summary = "\n\n".join(summary_lines)
            return ServiceResult.success(summary)

        except Exception as e:
            error_msg = f"Failed to get chapter summary: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def get_chapter_page_ranges(
        self, chapters: Chapters, max_page_number: int
    ) -> ServiceResult:
        """
        Calculate page ranges for each chapter.

        Args:
            chapters: Chapters object
            max_page_number: Maximum page number in the document

        Returns:
            ServiceResult with list of (start_page, end_page) tuples
        """
        try:
            self._log_info("Calculating chapter page ranges")

            if not chapters.chapters:
                return ServiceResult.failure("No chapters configured")

            # Get sorted list of chapter start pages
            chapter_pages = []
            for config in chapters.chapters.values():
                chapter_pages.append(config.page_number)

            chapter_pages.sort()

            # Calculate ranges
            ranges = []
            for i, start_page in enumerate(chapter_pages):
                if i < len(chapter_pages) - 1:
                    end_page = chapter_pages[i + 1] - 1
                else:
                    end_page = max_page_number

                ranges.append((start_page, end_page))

            self._log_info(f"Calculated {len(ranges)} chapter ranges")
            return ServiceResult.success(ranges)

        except Exception as e:
            error_msg = f"Failed to calculate chapter page ranges: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def get_page_content(self, filename: str, page_number: int) -> ServiceResult:
        """
        Get content (text and image path) for a specific page.

        Args:
            filename: The name of the PDF file
            page_number: Page number to retrieve

        Returns:
            ServiceResult with page content
        """
        try:
            self._log_info(f"Getting content for page {page_number}")

            text_path = resolve_text_path(filename, page_number)
            image_path = resolve_image_path(filename, page_number)

            if not text_path.exists():
                return ServiceResult.failure(
                    f"Text file not found for page {page_number}"
                )

            if not image_path.exists():
                return ServiceResult.failure(
                    f"Image file not found for page {page_number}"
                )

            with open(text_path, "r", encoding="utf-8") as f:
                text_content = f.read()

            content = {
                "page_number": page_number,
                "text": text_content,
                "image_path": str(image_path),
                "text_path": str(text_path),
            }

            return ServiceResult.success(content)

        except Exception as e:
            error_msg = f"Failed to get page content: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)
