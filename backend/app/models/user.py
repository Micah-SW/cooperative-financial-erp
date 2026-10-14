"""
User ORM Model.

Entity: User
Schema: coop.users
Module: Core

See: database_schema.md → coop.users
See: domain_model.md → User

TODO (Gemini):
    - Implement using SQLAlchemy 2.0 Mapped[] style
    - Inherit from CoopBase
    - Fields: id, username, email, password_hash, full_name, role, is_active, last_login, created_at
    - Constraints: UNIQUE(username), UNIQUE(email)
    - role uses UserRole enum
    - This table must be created FIRST (other tables reference it via created_by)
"""

# class User(CoopBase):
#     __tablename__ = "users"
#     __table_args__ = {"schema": "coop"}
#     ...
