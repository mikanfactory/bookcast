from bookcast.entities.project import Project


class ProjectRepository:
    def __init__(self, db):
        self.db = db

    def find(self, project_id: int) -> Project:
        response = self.db.table("project").select("*").eq("id", project_id).execute()
        if len(response.data):
            return Project(**response.data[0])
        raise ValueError(f"Project id {project_id} not found")

    def select_all(self) -> list[Project]:
        response = self.db.table("project").select("*").execute()
        if len(response.data):
            return [Project(**item) for item in response.data]
        return []

    def create(self, project: Project) -> Project:
        exclude_fields = {"id", "created_at", "updated_at"}
        response = self.db.table("project").insert(project.model_dump(exclude=exclude_fields)).execute()
        if len(response.data) == 1:
            return Project(**response.data[0])
        raise RuntimeError(f"Failed to create project: {project}, response: {response}")

    def update(self, project: Project) -> Project:
        exclude_fields = {"id", "created_at", "updated_at"}
        response = (
            self.db.table("project").update(project.model_dump(exclude=exclude_fields)).eq("id", project.id).execute()
        )
        if len(response.data):
            return Project(**response.data[0])
        raise RuntimeError(f"Failed to update project: {project}, response: {response}")
