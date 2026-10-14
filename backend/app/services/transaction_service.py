"""
Transaction Service (Internal).

Module: Finance
See: service_contracts.md → TransactionService

CRITICAL: This service is NOT directly exposed via API.
It is used INTERNALLY by other services to create ledger entries.

Responsibility:
    - Create immutable transaction records
    - Calculate and set balance_after
    - Update fund.current_balance atomically
    - Create reversal transactions
"""


class TransactionService:
    """
    Internal financial ledger service — the ONLY way to create transactions.

    Responsibilities:
        - Insert immutable transaction record
        - Calculate new balance_after
        - Update fund.current_balance atomically
        - Validate fund has sufficient balance for DEBITs
        - Create reversal transactions (opposite direction)

    Must NOT:
        - Update or delete existing transactions
        - Commit the DB transaction (caller controls boundary)
        - Be called directly from API routers
        - Allow negative fund balances without explicit check

    Called by:
        - ContributionService.record_contribution()
        - ContributionService.reverse_contribution()
        - WithdrawalService.mark_paid()
        - MemberService.exit_member()
        - PropertyService.record_rental_income()
        - ExpenseService.record_expense()
        - FundService.transfer()
    """

    async def create_transaction(self, db, *, fund_id, transaction_type, amount,
                                  direction, member_id=None, reference_type=None,
                                  reference_id=None, reversal_of=None,
                                  description, transaction_date, user_id):
        """
        Create immutable ledger entry + update fund balance.
        Does NOT commit. Caller controls transaction boundary.
        TODO (Gemini): Implement per service_contracts.md
        """
        pass

    async def create_reversal(self, db, *, original_transaction_id, reason, user_id):
        """
        Create reversal (opposite direction, same amount, reversal_of = original).
        TODO (Gemini): Implement
        """
        pass

    async def list_transactions(self, db, *, filters=None, page=1, per_page=50):
        """Read-only listing. TODO (Gemini): Implement"""
        pass
