from enum import StrEnum


class SessionState(StrEnum):
    filename = "_filename"
    page_number = "_page_number"
    max_page_number = "_max_page_number"
    chapters = "_chapters"
