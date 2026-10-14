"""
Contribution Service.

Module: Finance
See: service_contracts.md → ContributionService

Responsibility:
    - Record contributions (creates 2 transactions atomically)
    - Verify contributions against bank deposits
    - Reverse contributions (creates reversal transactions)
"""


class ContributionService:
    """
    Handles contribution recording, verification, and reversal workflows.

    Responsibilities:
        - Validate member exists and is ACTIVE
        - Create contribution record
        - Create CREDIT transaction on Member Equity Fund (member_amount)
        - Create CREDIT transaction on Operating Fund (operating_amount)
        - Verify contributions (RECORDED → VERIFIED)
        - Reverse contributions (creates REVERSAL transactions)

    Must NOT:
        - Directly edit historical transactions
        - Bypass the TransactionService
        - Derive amounts from current config (amounts are passed explicitly)
    """

    async def list_contributions(self, db, *, member_id=None, status=None, period=None,
                                  from_date=None, to_date=None, page=1, per_page=25):
        """List with filters. TODO (Gemini): Implement"""
        pass

    async def record_contribution(self, db, data, user_id):
        """
        ATOMIC: contribution + 2 transactions + fund balance updates + audit.
        TODO (Gemini): Implement per service_contracts.md
        """
        pass

    async def verify_contribution(self, db, contribution_id, data, user_id):
        """RECORDED → VERIFIED. TODO (Gemini): Implement"""
        pass

    async def reverse_contribution(self, db, contribution_id, reason, user_id):
        """
        ATOMIC: status→DISPUTED + 2 reversal transactions + audit.
        TODO (Gemini): Implement per service_contracts.md
        """
        pass
