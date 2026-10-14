"""
Transaction ORM Model (Core Ledger).

Entity: Transaction
Schema: coop.transactions
Module: Finance

See: database_schema.md → coop.transactions
See: domain_model.md → Transaction

CRITICAL BUSINESS RULES:
    - Transactions are IMMUTABLE — NEVER updated or deleted
    - Corrections: REVERSAL (opposite direction) + new CORRECTION transaction
    - balance_after provides running balance per fund
    - amount is ALWAYS positive; direction indicates CREDIT or DEBIT
    - reference_type + reference_id creates polymorphic link to source document
    - PostgreSQL trigger should PREVENT direct UPDATE/DELETE as safety net

TODO (Gemini):
    - Fields: id, fund_id (FK→funds), transaction_type, amount, direction,
              balance_after, member_id (FK→members, nullable), reference_type,
              reference_id, reversal_of (FK→transactions, nullable), description,
              transaction_date, created_at, created_by (FK→users)
    - CHECK: amount > 0
    - CHECK: direction IN ('CREDIT', 'DEBIT')
    - Indexes: fund_id, member_id, transaction_type, transaction_date,
               (reference_type, reference_id), reversal_of, (fund_id, transaction_date)
"""

# class Transaction(CoopBase):
#     __tablename__ = "transactions"
#     __table_args__ = {"schema": "coop"}
#     ...
