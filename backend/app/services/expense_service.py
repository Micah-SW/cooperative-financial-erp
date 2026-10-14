"""
Expense Service.

Module: Expense
See: service_contracts.md → ExpenseService
"""


class ExpenseService:
    """
    Records cooperative expenses with fund debit transactions.

    Responsibilities:
        - Record expenses against active funds
        - Create DEBIT transaction on specified fund
        - Validate fund has sufficient balance
        - Categorize expenses
        - Optionally link to projects

    Must NOT:
        - Allow spending beyond fund balance (raise InsufficientFundsError)
        - Bypass TransactionService for financial operations
    """

    async def list_expenses(self, db, *, fund_id=None, category=None,
                             from_date=None, to_date=None, project_id=None,
                             page=1, per_page=25):
        """List with filters. TODO (Gemini): Implement"""
        pass

    async def record_expense(self, db, data, user_id):
        """
        ATOMIC: Expense record + DEBIT transaction + fund balance update + audit.
        TODO (Gemini): Implement per service_contracts.md
        """
        pass
