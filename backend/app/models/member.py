"""
Member ORM Model.

Entity: Member
Schema: coop.members
Module: Member

See: database_schema.md → coop.members
See: domain_model.md → Member

Business Rules:
    - member_number is immutable after creation
    - Status transitions: ACTIVE → EXITED (one-way)
    - Exited members are never physically deleted
    - Historical transactions persist after exit
    - Members cannot share accounts

TODO (Gemini):
    - Implement using SQLAlchemy 2.0 Mapped[] style
    - Inherit from CoopBase
    - Fields: id, member_number, full_name, phone, email, address,
              date_joined, date_exited, status, exit_reason, notes,
              created_at, updated_at, created_by (FK→users)
    - Constraints: UNIQUE(member_number)
    - Relationships: shares, contributions, withdrawals, transactions
    - Index on status
"""

# class Member(CoopBase):
#     __tablename__ = "members"
#     __table_args__ = {"schema": "coop"}
#     ...
