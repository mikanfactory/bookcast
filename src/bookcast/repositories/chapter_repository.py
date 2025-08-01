from bookcast.entities.chapter import Chapter


class ChapterRepository:
    def __init__(self, db):
        self.db = db

    def find(self, chapter_id: int):
        response = self.db.table("chapter").select("*").eq("id", chapter_id).execute()
        return response

    def select_by_project_id(self, project_id: int):
        response = self.db.table("chapter").select("*").eq("project_id", project_id).execute()
        return response

    def create(self, chapter: Chapter):
        exclude_fields = {"id", "extracted_text", "created_at", "updated_at"}
        response = self.db.table("chapter").insert(chapter.model_dump(exclude=exclude_fields)).execute()
        return response

    def update(self, chapter: Chapter):
        exclude_fields = {"updated_at"}
        response = (
            self.db.table("chapter").update(chapter.model_dump(exclude=exclude_fields)).eq("id", chapter.id).execute()
        )
        return response

    def delete(self, chapter_id: int):
        response = self.db.table("chapter").delete().eq("id", chapter_id).execute()
        return response
