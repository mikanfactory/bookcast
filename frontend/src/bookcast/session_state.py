from enum import StrEnum


class SessionState(StrEnum):
    project = "_project"
    image_dir = "_image_dir"

    # Chapter Page
    current_page = "_current_page"
    selected_chapter_number = "_selected_chapter_number"

    # Podcast Page
    downloaded_from_server = "_downloaded_from_server"
    downloaed_path = "_downloaded_path"
