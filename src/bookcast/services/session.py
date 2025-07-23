"""
Session management service for handling Streamlit session state.
"""

from typing import Any, Optional

import streamlit as st

from bookcast.view_models import Chapters, PodcastSetting
from bookcast.services.base import BaseService, ServiceResult
from bookcast.session_state import ChapterPageSessionState, SessionState


class SessionService(BaseService):
    """Service for managing Streamlit session state."""

    def get_session_value(self, key: str, default: Any = None) -> Any:
        """
        Get value from session state.

        Args:
            key: Session state key
            default: Default value if key doesn't exist

        Returns:
            Value from session state or default
        """
        return st.session_state.get(key, default)

    def set_session_value(self, key: str, value: Any) -> ServiceResult:
        """
        Set value in session state.

        Args:
            key: Session state key
            value: Value to set

        Returns:
            ServiceResult indicating success
        """
        try:
            st.session_state[key] = value
            return ServiceResult.success({"key": key, "value": value})
        except Exception as e:
            error_msg = f"Failed to set session value: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def clear_session_value(self, key: str) -> ServiceResult:
        """
        Clear value from session state.

        Args:
            key: Session state key to clear

        Returns:
            ServiceResult indicating success
        """
        try:
            if key in st.session_state:
                del st.session_state[key]
            return ServiceResult.success({"key": key, "cleared": True})
        except Exception as e:
            error_msg = f"Failed to clear session value: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def get_filename(self) -> Optional[str]:
        """Get the current filename from session state."""
        return self.get_session_value(SessionState.filename)

    def set_filename(self, filename: str) -> ServiceResult:
        """Set the current filename in session state."""
        return self.set_session_value(SessionState.filename, filename)

    def get_max_page_number(self) -> Optional[int]:
        """Get the maximum page number from session state."""
        return self.get_session_value(SessionState.max_page_number)

    def set_max_page_number(self, max_page: int) -> ServiceResult:
        """Set the maximum page number in session state."""
        return self.set_session_value(SessionState.max_page_number, max_page)

    def get_chapters(self) -> Chapters:
        """Get the chapters configuration from session state."""
        chapters = self.get_session_value(SessionState.chapters)
        return chapters if chapters else Chapters()

    def set_chapters(self, chapters: Chapters) -> ServiceResult:
        """Set the chapters configuration in session state."""
        return self.set_session_value(SessionState.chapters, chapters)

    def get_podcast_setting(self) -> Optional[PodcastSetting]:
        """Get the podcast setting from session state."""
        return self.get_session_value(SessionState.podcast_setting)

    def set_podcast_setting(self, setting: PodcastSetting) -> ServiceResult:
        """Set the podcast setting in session state."""
        return self.set_session_value(SessionState.podcast_setting, setting)

    def get_podcast_script(self) -> Optional[str]:
        """Get the podcast script from session state."""
        return self.get_session_value(SessionState.podcast_script)

    def set_podcast_script(self, script: str) -> ServiceResult:
        """Set the podcast script in session state."""
        return self.set_session_value(SessionState.podcast_script, script)

    def get_current_page(self) -> int:
        """Get the current page number from session state."""
        return self.get_session_value(ChapterPageSessionState.current_page, 1)

    def set_current_page(self, page: int) -> ServiceResult:
        """Set the current page number in session state."""
        return self.set_session_value(ChapterPageSessionState.current_page, page)

    def initialize_session(
        self, filename: str = None, max_page: int = None
    ) -> ServiceResult:
        """
        Initialize session state with default values.

        Args:
            filename: Optional filename to set
            max_page: Optional max page number to set

        Returns:
            ServiceResult with initialization status
        """
        try:
            self._log_info("Initializing session state")

            # Initialize with provided values or defaults
            if filename and not self.get_filename():
                self.set_filename(filename)

            if max_page and not self.get_max_page_number():
                self.set_max_page_number(max_page)

            # Initialize chapters if not exists
            if not self.get_session_value(SessionState.chapters):
                self.set_chapters(Chapters())

            # Initialize current page if not exists
            if not self.get_session_value(ChapterPageSessionState.current_page):
                self.set_current_page(1)

            session_info = {
                "filename": self.get_filename(),
                "max_page": self.get_max_page_number(),
                "current_page": self.get_current_page(),
                "chapters": self.get_chapters(),
            }

            self._log_info("Session state initialized successfully")
            return ServiceResult.success(session_info)

        except Exception as e:
            error_msg = f"Failed to initialize session: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def get_session_summary(self) -> ServiceResult:
        """
        Get a summary of current session state.

        Returns:
            ServiceResult with session summary
        """
        try:
            summary = {
                "filename": self.get_filename(),
                "max_page_number": self.get_max_page_number(),
                "current_page": self.get_current_page(),
                "chapters": self.get_chapters(),
                "podcast_setting": self.get_podcast_setting(),
                "has_podcast_script": bool(self.get_podcast_script()),
            }

            return ServiceResult.success(summary)

        except Exception as e:
            error_msg = f"Failed to get session summary: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)

    def validate_session_state(self) -> ServiceResult:
        """
        Validate that session state has required values.

        Returns:
            ServiceResult with validation status
        """
        try:
            issues = []

            if not self.get_filename():
                issues.append("Filename not set")

            if not self.get_max_page_number():
                issues.append("Max page number not set")

            chapters = self.get_chapters()
            if not chapters.chapters:
                issues.append("No chapters configured")

            if issues:
                return ServiceResult.failure(
                    f"Session validation failed: {', '.join(issues)}"
                )

            return ServiceResult.success({"valid": True, "issues": []})

        except Exception as e:
            error_msg = f"Failed to validate session state: {str(e)}"
            self._log_error(error_msg)
            return ServiceResult.failure(error_msg)
