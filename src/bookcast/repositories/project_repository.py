from bookcast.entities.project import Project


class ProjectRepository:
    def __init__(self, db):
        self.db = db

    def find(self, project_id: int):
        response = self.db.table("project").select("*").eq("id", project_id).execute()
        return response

    def create(self, project: Project):
        exclude_fields = {"id", "created_at", "updated_at"}
        response = self.db.table("project").insert(project.model_dump(exclude=exclude_fields)).execute()
        return response

    def update(self, project: Project):
        exclude_fields = {"id", "created_at", "updated_at"}
        response = (
            self.db.table("project").update(project.model_dump(exclude=exclude_fields)).eq("id", project.id).execute()
        )
        return response
