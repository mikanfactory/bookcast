from bookcast.entities.project import Project


class ProjectRepository:
    def __init__(self, db):
        self.db = db

    def find(self, project_id: int):
        response = self.db.table("project").select("*").eq("id", project_id).execute()
        return response

    def insert_project(self, project: Project):
        response = self.db.table("project").insert(project.model_dump(exclude=["id", "created_at"])).execute()
        return response

    def update(self, project: Project):
        response = self.db.table("project").update(project.model_dump()).eq("id", project.id).execute()
        return response
