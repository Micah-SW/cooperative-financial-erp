"""
Project ORM Model.

Entity: Project
Schema: coop.projects
Module: Property

See: database_schema.md → coop.projects
See: domain_model.md → Project

TODO (Gemini):
    - Fields: id, name, description, status (ProjectStatus), budget,
              actual_cost, start_date, end_date, notes, created_at, created_by (FK→users)
    - Status lifecycle: PLANNING → UNDER_CONSTRUCTION → OPERATIONAL → COMPLETED
"""

# class Project(CoopBase):
#     __tablename__ = "projects"
#     __table_args__ = {"schema": "coop"}
#     ...
