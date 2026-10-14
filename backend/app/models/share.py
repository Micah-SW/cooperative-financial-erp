"""
Share ORM Model.

Entity: Share
Schema: coop.shares
Module: Member

See: database_schema.md → coop.shares
See: domain_model.md → Share

Business Rules:
    - Share records are append-only (changes create new records)
    - Shares are NOT transferable between members
    - On member exit: final record with share_count=0
    - total_value = share_count × value_per_share (CHECK constraint)
    - Current: 12 shares × 5,000 ETB = 60,000 ETB (configurable)

TODO (Gemini):
    - Implement using SQLAlchemy 2.0 Mapped[] style
    - Inherit from CoopBase
    - Fields: id, member_id (FK→members), share_count, value_per_share,
              total_value, effective_date, created_at, created_by (FK→users)
    - CHECK: share_count >= 0
    - CHECK: total_value = share_count * value_per_share
"""

# class Share(CoopBase):
#     __tablename__ = "shares"
#     __table_args__ = {"schema": "coop"}
#     ...
