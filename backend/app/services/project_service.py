"""
Project Service.

Module: Property
See: service_contracts.md (implied)
"""


class ProjectService:
    """
    Manages cooperative investment projects.

    Responsibilities:
        - CRUD for projects
        - Project status lifecycle management

    Must NOT:
        - Handle financial transactions directly
    """

    async def list_projects(self, db, *, page=1, per_page=25):
        """TODO (Gemini): Implement"""
        pass

    async def get_project(self, db, project_id):
        """TODO (Gemini): Implement"""
        pass

    async def create_project(self, db, data, user_id):
        """TODO (Gemini): Implement"""
        pass

    async def update_project(self, db, project_id, data, user_id):
        """TODO (Gemini): Implement"""
        pass
