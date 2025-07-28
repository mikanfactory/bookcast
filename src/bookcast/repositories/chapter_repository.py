from bookcast.entities.chapter import Chapter


class ChapterRepository:
    def __init__(self, db):
        self.db = db

    def get_chapter_by_id(self, chapter_id: int):
        response = self.db.table("chapter").select("*").eq("id", chapter_id).execute()
        return response

    def insert_chapter(self, chapter: Chapter):
        response = self.db.table("chapter").insert(chapter.model_dump(exclude=["id", "created_at"])).execute()
        return response
