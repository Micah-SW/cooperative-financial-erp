"""
SQLAlchemy ORM Models — Central Import Registry.

All models MUST be imported here so Alembic can discover them for migrations.
"""

from app.models.audit_log import AuditLog
from app.models.base import CoopBase
from app.models.member import Member
from app.models.share import Share
from app.models.system_config import SystemConfig
from app.models.user import User

__all__ = [
    "AuditLog",
    "CoopBase",
    "Member",
    "Share",
    "SystemConfig",
    "User",
]

# Downstream models reserved for future chapters:
# from app.models.contribution import Contribution
# from app.models.withdrawal import Withdrawal
# from app.models.transaction import Transaction
# from app.models.fund import Fund, FundTransfer
# from app.models.bank_account import BankAccount
# from app.models.project import Project
# from app.models.property import Property
# from app.models.rental import RentalUnit, RentalIncome
# from app.models.expense import Expense
