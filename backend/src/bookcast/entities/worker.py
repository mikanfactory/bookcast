from pydantic import BaseModel


class OCRWorkerResult(BaseModel):
    chapter_id: int
    page_number: int
    extracted_text: str
