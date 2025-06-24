from enum import StrEnum


class SessionState(StrEnum):
    filename = "_filename"
    max_page_number = "_max_page_number"
    chapters = "_chapters"
    podcast_setting = "_podcast_setting"
    podcast_script = "_podcast_script"


class ChapterPageSessionState(StrEnum):
    current_page = "_current_page"
    chapter_select = "_chapter_select"
