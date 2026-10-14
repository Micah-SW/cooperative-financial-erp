"""
Withdrawal Service.

Module: Finance
See: service_contracts.md → WithdrawalService
"""


class WithdrawalService:
    """
    Manages withdrawal request lifecycle: creation through payment.

    Responsibilities:
        - Create withdrawal requests (validate balance sufficiency)
        - Approve withdrawals (ADMIN only)
        - Reject withdrawals with reason
        - Mark as paid (creates DEBIT transaction)

    Must NOT:
        - Create transactions on create or approve (only on mark_paid)
        - Allow withdrawal amount > member balance
        - Process PARTIAL_WITHDRAWAL if UBR-8 is not enabled
    """

    async def create_withdrawal(self, db, data, user_id):
        """Create PENDING request. TODO (Gemini): Implement"""
        pass

    async def approve_withdrawal(self, db, withdrawal_id, user_id):
        """PENDING → APPROVED. TODO (Gemini): Implement"""
        pass

    async def reject_withdrawal(self, db, withdrawal_id, reason, user_id):
        """PENDING → REJECTED. TODO (Gemini): Implement"""
        pass

    async def mark_paid(self, db, withdrawal_id, data, user_id):
        """
        APPROVED → PAID. Creates DEBIT transaction on MEMBER_EQUITY.
        TODO (Gemini): Implement per service_contracts.md
        """
        pass
