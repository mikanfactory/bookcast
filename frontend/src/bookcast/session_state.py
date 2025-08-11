from enum import StrEnum


class SessionState(StrEnum):
    project_id = "_project_id"
    image_dir = "_image_dir"
    filename = "_filename"
    max_page_number = "_max_page_number"
    project = "_project"
    podcast_setting = "_podcast_setting"
    podcast_script = "_podcast_script"

    # Chapter Page
    current_page = "_current_page"
    chapter_select = "_chapter_select"
    selected_chapter_num = "_selected_chapter_num"
