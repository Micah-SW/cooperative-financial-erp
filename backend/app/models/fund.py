"""
Fund ORM Model.

Entity: Fund
Schema: coop.funds
Module: Finance

See: database_schema.md → coop.funds
See: domain_model.md → Fund

Business Rules:
    - current_balance is DENORMALIZED for performance
    - Authoritative balance is always SUM(transactions)
    - Reconciliation check should run periodically
    - Seeded at setup: MEMBER_EQUITY, OPERATING, PROJECT, RENTAL_INCOME
    - Fund balances must never go negative without explicit approval

TODO (Gemini):
    - Fields: id, name, fund_type, description, current_balance, is_active, created_at
    - UNIQUE(name)

Also includes FundTransfer model.

FundTransfer Business Rules:
    - Creates exactly TWO transactions: FUND_TRANSFER_OUT + FUND_TRANSFER_IN
    - Atomic: both succeed or neither
    - source_fund_id != destination_fund_id (CHECK constraint)

TODO (Gemini):
    - FundTransfer fields: id, source_fund_id (FK→funds), destination_fund_id (FK→funds),
                           amount, description, transfer_date, created_at, created_by (FK→users)
"""

# class Fund(CoopBase):
#     __tablename__ = "funds"
#     __table_args__ = {"schema": "coop"}
#     ...

# class FundTransfer(CoopBase):
#     __tablename__ = "fund_transfers"
#     __table_args__ = {"schema": "coop"}
#     ...
