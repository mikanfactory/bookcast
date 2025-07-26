from typing import Any, Optional

import streamlit as st

from bookcast.services.base import BaseService, ServiceResult
from bookcast.session_state import ChapterPageSessionState, SessionState
from bookcast.view_models import Chapters, PodcastSetting


class SessionService(BaseService):
    def get_session_value(self, key: str, default: Any = None) -> Any:
        return st.session_state.get(key, default)

    def set_session_value(self, key: str, value: Any) -> ServiceResult:
        st.session_state[key] = value
        return ServiceResult.success({"key": key, "value": value})

    def clear_session_value(self, key: str) -> ServiceResult:
        if key in st.session_state:
            del st.session_state[key]

    def get_filename(self) -> Optional[str]:
        return self.get_session_value(SessionState.filename)

    def set_filename(self, filename: str) -> ServiceResult:
        return self.set_session_value(SessionState.filename, filename)

    def get_max_page_number(self) -> Optional[int]:
        return self.get_session_value(SessionState.max_page_number)

    def set_max_page_number(self, max_page: int) -> ServiceResult:
        return self.set_session_value(SessionState.max_page_number, max_page)

    def get_chapters(self) -> Chapters:
        chapters = self.get_session_value(SessionState.chapters)
        return chapters if chapters else Chapters()

    def set_chapters(self, chapters: Chapters) -> ServiceResult:
        return self.set_session_value(SessionState.chapters, chapters)

    def get_podcast_setting(self) -> Optional[PodcastSetting]:
        return self.get_session_value(SessionState.podcast_setting)

    def set_podcast_setting(self, setting: PodcastSetting) -> ServiceResult:
        return self.set_session_value(SessionState.podcast_setting, setting)

    def get_podcast_script(self) -> Optional[str]:
        return self.get_session_value(SessionState.podcast_script)

    def set_podcast_script(self, script: str) -> ServiceResult:
        return self.set_session_value(SessionState.podcast_script, script)

    def get_current_page(self) -> int:
        return self.get_session_value(ChapterPageSessionState.current_page, 1)

    def set_current_page(self, page: int) -> ServiceResult:
        return self.set_session_value(ChapterPageSessionState.current_page, page)

    def initialize_session(self, filename: str = None, max_page: int = None):
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
        summary = {
            "filename": self.get_filename(),
            "max_page_number": self.get_max_page_number(),
            "current_page": self.get_current_page(),
            "chapters": self.get_chapters(),
            "podcast_setting": self.get_podcast_setting(),
            "has_podcast_script": bool(self.get_podcast_script()),
        }

        return ServiceResult.success(summary)

    def validate_session_state(self) -> ServiceResult:
        issues = []

        if not self.get_filename():
            issues.append("Filename not set")

        if not self.get_max_page_number():
            issues.append("Max page number not set")

        chapters = self.get_chapters()
        if not chapters.chapters:
            issues.append("No chapters configured")

        if issues:
            return ServiceResult.failure(f"Session validation failed: {', '.join(issues)}")

        return ServiceResult.success({"valid": True, "issues": []})
