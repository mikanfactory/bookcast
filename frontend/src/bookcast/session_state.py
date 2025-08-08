from enum import StrEnum


class SessionState(StrEnum):
    project_id = "_project_id"
    images = "_images"
    filename = "_filename"
    chapters = "_chapters"
    podcast_setting = "_podcast_setting"
    podcast_script = "_podcast_script"

    # Chapter Page
    current_page = "_current_page"
    chapter_select = "_chapter_select"
