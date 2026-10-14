"""
Report Service.

Module: Reporting
See: service_contracts.md → ReportService

Responsibility:
    - Provide read-only aggregated financial views
    - All reports are real-time queries (no materialized views in v1)
"""


class ReportService:
    """
    Read-only reporting and analytics.

    Responsibilities:
        - Member balance report (all members with accumulated balances)
        - Contribution summary (per-member totals by period)
        - Fund summary (income/expense/net by fund by period)
        - Rental income summary (by property/unit by period)
        - Expense summary (by category by period)
        - Member statement (chronological transactions with running balance)
        - Dashboard metrics (key financial indicators)

    Must NOT:
        - Mutate any data
        - Create transactions or records
        - Perform financial calculations differently from other services
          (balance formula must match MemberService.get_member_balance)
    """

    async def member_balances(self, db):
        """All active members with accumulated balances. TODO (Gemini): Implement"""
        pass

    async def contribution_summary(self, db, *, period=None, from_date=None, to_date=None):
        """Aggregate contributions by member for period. TODO (Gemini): Implement"""
        pass

    async def fund_summary(self, db, *, from_date=None, to_date=None):
        """All funds with period income/expense/net. TODO (Gemini): Implement"""
        pass

    async def rental_income_summary(self, db, *, from_date=None, to_date=None):
        """By property/unit. TODO (Gemini): Implement"""
        pass

    async def expense_summary(self, db, *, from_date=None, to_date=None, fund_id=None):
        """By category. TODO (Gemini): Implement"""
        pass

    async def member_statement(self, db, member_id, *, from_date=None, to_date=None):
        """Chronological transactions with running balance. TODO (Gemini): Implement"""
        pass

    async def dashboard_metrics(self, db):
        """Key financial indicators for dashboard. TODO (Gemini): Implement"""
        pass
