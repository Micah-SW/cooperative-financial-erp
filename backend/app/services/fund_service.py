"""
Fund Service.

Module: Finance
See: service_contracts.md → FundService
"""


class FundService:
    """
    Manages fund accounts, transfers, and reconciliation.

    Responsibilities:
        - List funds with current balances
        - Fund detail with recent transactions
        - Inter-fund transfers (creates paired DEBIT/CREDIT transactions)
        - Balance reconciliation (compare cached vs computed)

    Must NOT:
        - Allow transfer where source == destination
        - Allow transfers exceeding source balance
        - Create transactions directly (uses TransactionService)
    """

    async def list_funds(self, db):
        """All funds with balances. TODO (Gemini): Implement"""
        pass

    async def get_fund(self, db, fund_id):
        """Fund detail. TODO (Gemini): Implement"""
        pass

    async def get_fund_transactions(self, db, fund_id, *, from_date=None, to_date=None,
                                     type=None, page=1, per_page=50):
        """Paginated transaction history. TODO (Gemini): Implement"""
        pass

    async def transfer(self, db, data, user_id):
        """
        ATOMIC: FundTransfer + DEBIT on source + CREDIT on destination.
        TODO (Gemini): Implement per service_contracts.md
        """
        pass

    async def reconcile_fund(self, db, fund_id):
        """
        Compare fund.current_balance vs SUM(transactions). Read-only diagnostic.
        TODO (Gemini): Implement
        """
        pass
