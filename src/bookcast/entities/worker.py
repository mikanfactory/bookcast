from pydantic import BaseModel


class OCRWorkerResult(BaseModel):
    chapter_id: int
    page_number: int
    extracted_text: str


class ScriptWritingWorkerResult(BaseModel):
    chapter_id: int
    script: str


class TTSWorkerResult(BaseModel):
    chapter_id: int
    index: int
