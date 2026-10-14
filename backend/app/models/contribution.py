"""
Contribution ORM Model.

Entity: Contribution
Schema: coop.contributions
Module: Finance

See: database_schema.md → coop.contributions
See: domain_model.md → Contribution

Business Rules:
    - Recording creates TWO transactions (member equity + operating)
    - Split amounts are snapshotted at time of contribution
    - total_amount = member_amount + operating_amount (CHECK constraint)
    - Corrections use reversal transactions, not UPDATEs
    - Status flow: RECORDED → VERIFIED, or RECORDED/VERIFIED → DISPUTED (via reversal)

TODO (Gemini):
    - Fields: id, member_id (FK→members), contribution_date, member_amount,
              operating_amount, total_amount, bank_reference, status,
              verified_by (FK→users), verified_at, period_label, notes,
              created_at, created_by (FK→users)
    - All monetary fields: Numeric(15, 2)
"""

# class Contribution(CoopBase):
#     __tablename__ = "contributions"
#     __table_args__ = {"schema": "coop"}
#     ...
