"""
BankAccount ORM Model.

Entity: BankAccount
Schema: coop.bank_accounts
Module: Finance

See: database_schema.md → coop.bank_accounts
See: domain_model.md → BankAccount

Business Rules:
    - Reference entity for bank reconciliation
    - Not directly linked to funds in v1 (manual association)

TODO (Gemini):
    - Fields: id, account_name, bank_name, account_number, purpose, is_active, created_at
"""

# class BankAccount(CoopBase):
#     __tablename__ = "bank_accounts"
#     __table_args__ = {"schema": "coop"}
#     ...
