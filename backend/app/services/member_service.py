"""
Member Service.

Module: Member
See: service_contracts.md → MemberService

Responsibility:
    - Member CRUD (create, read, update — never delete)
    - Share tracking
    - Member exit processing
    - Member balance calculation
"""


class MemberService:
    """
    Manages member lifecycle: registration through exit.

    Responsibilities:
        - Create members with initial share assignment
        - Update mutable member fields
        - Calculate member accumulated balance from transactions
        - Process member exit atomically (status, shares, withdrawal, transaction)

    Must NOT:
        - Delete members
        - Allow member_number changes after creation
        - Bypass TransactionService for financial operations
        - Silently invent exit payout formulas (UBR-1)
    """

    async def list_members(self, db, *, status=None, search=None, page=1, per_page=25):
        """List with optional filters. TODO (Gemini): Implement"""
        pass

    async def get_member(self, db, member_id):
        """Full detail with shares + balance. TODO (Gemini): Implement"""
        pass

    async def create_member(self, db, data, user_id):
        """Create member + initial shares. TODO (Gemini): Implement"""
        pass

    async def update_member(self, db, member_id, data, user_id):
        """Update mutable fields. TODO (Gemini): Implement"""
        pass

    async def exit_member(self, db, member_id, data, user_id):
        """
        ATOMIC: status→EXITED, shares→0, withdrawal created, transaction created.
        TODO (Gemini): Implement per service_contracts.md
        """
        pass

    async def get_member_balance(self, db, member_id):
        """
        SUM(CREDIT) - SUM(DEBIT) for this member on MEMBER_EQUITY fund.
        This is the CANONICAL balance calculation.
        TODO (Gemini): Implement
        """
        pass
