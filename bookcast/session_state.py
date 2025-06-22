from enum import StrEnum


class SessionState(StrEnum):
    filename = "_filename"
    max_page_number = "_max_page_number"
    chapters = "_chapters"


class ChapterPageSessionState(StrEnum):
    current_page = "_current_page"
    chapter_select = "_chapter_select"
