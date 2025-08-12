from bookcast.entities.chapter import Chapter


class ChapterRepository:
    def __init__(self, db):
        self.db = db

    def find(self, chapter_id: int) -> Chapter | None:
        response = self.db.table("chapter").select("*").eq("id", chapter_id).execute()
        if len(response.data):
            return Chapter(**response.data[0])
        return None

    def select_chapter_by_project_id(self, project_id: int) -> list[Chapter]:
        response = self.db.table("chapter").select("*").eq("project_id", project_id).execute()
        if len(response.data):
            return [Chapter(**item) for item in response.data]
        return []

    def create(self, chapter: Chapter) -> Chapter | None:
        exclude_fields = {"id", "extracted_text", "created_at", "updated_at"}
        response = self.db.table("chapter").insert(chapter.model_dump(exclude=exclude_fields)).execute()
        if len(response.data):
            return Chapter(**response.data[0])
        return None

    def bulk_create(self, chapters: list[Chapter]) -> list[Chapter]:
        exclude_fields = {"id", "extracted_text", "created_at", "updated_at"}
        data = [chapter.model_dump(exclude=exclude_fields) for chapter in chapters]
        response = self.db.table("chapter").insert(data).execute()
        if len(response.data):
            return [Chapter(**item) for item in response.data]
        return []

    def update(self, chapter: Chapter) -> Chapter | None:
        exclude_fields = {"id", "created_at", "updated_at"}
        response = (
            self.db.table("chapter").update(chapter.model_dump(exclude=exclude_fields)).eq("id", chapter.id).execute()
        )
        if len(response.data):
            return Chapter(**response.data[0])
        return None

    def delete(self, chapter_id: int):
        response = self.db.table("chapter").delete().eq("id", chapter_id).execute()
        return response
