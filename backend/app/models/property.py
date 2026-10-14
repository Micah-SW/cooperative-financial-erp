"""
Property ORM Model.

Entity: Property
Schema: coop.properties
Module: Property

See: database_schema.md → coop.properties
See: domain_model.md → Property

TODO (Gemini):
    - Fields: id, project_id (FK→projects, nullable), name, address,
              property_type, is_active, notes, created_at
    - Index on project_id
"""

# class Property(CoopBase):
#     __tablename__ = "properties"
#     __table_args__ = {"schema": "coop"}
#     ...
