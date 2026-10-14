"""
Withdrawal ORM Model.

Entity: Withdrawal
Schema: coop.withdrawals
Module: Finance

See: database_schema.md → coop.withdrawals
See: domain_model.md → Withdrawal

Business Rules:
    - Status flow: PENDING → APPROVED → PAID, or PENDING → REJECTED
    - Transaction is created ONLY on mark_paid (not on create or approve)
    - EXIT_PAYOUT type triggers member status change to EXITED
    - PARTIAL_WITHDRAWAL is gated by UBR-8 config flag

TODO (Gemini):
    - Fields: id, member_id (FK→members), withdrawal_type, amount, status,
              requested_date, approved_by (FK→users), approved_at, paid_date,
              bank_reference, reason, notes, created_at, created_by (FK→users)
"""

# class Withdrawal(CoopBase):
#     __tablename__ = "withdrawals"
#     __table_args__ = {"schema": "coop"}
#     ...
