"""
Canonical enumerations for the Cooperative Financial Management ERP.

These enums are the SINGLE SOURCE OF TRUTH for all status values,
types, and categories used across models, schemas, and services.

DO NOT duplicate these definitions elsewhere.
"""

from enum import Enum


class MemberStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXITED = "EXITED"
    SUSPENDED = "SUSPENDED"  # Reserved for future use


class TransactionType(str, Enum):
    MEMBER_CONTRIBUTION = "MEMBER_CONTRIBUTION"
    OPERATING_CONTRIBUTION = "OPERATING_CONTRIBUTION"
    WITHDRAWAL = "WITHDRAWAL"
    EXIT_PAYOUT = "EXIT_PAYOUT"
    RENTAL_INCOME = "RENTAL_INCOME"
    EXPENSE = "EXPENSE"
    FUND_TRANSFER_IN = "FUND_TRANSFER_IN"
    FUND_TRANSFER_OUT = "FUND_TRANSFER_OUT"
    CORRECTION = "CORRECTION"
    REVERSAL = "REVERSAL"
    OPENING_BALANCE = "OPENING_BALANCE"


class TransactionDirection(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class FundType(str, Enum):
    MEMBER_EQUITY = "MEMBER_EQUITY"
    OPERATING = "OPERATING"
    PROJECT = "PROJECT"
    RENTAL_INCOME = "RENTAL_INCOME"
    RESERVE = "RESERVE"


class ContributionStatus(str, Enum):
    RECORDED = "RECORDED"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"


class WithdrawalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    REJECTED = "REJECTED"


class WithdrawalType(str, Enum):
    EXIT_PAYOUT = "EXIT_PAYOUT"
    PARTIAL_WITHDRAWAL = "PARTIAL_WITHDRAWAL"


class ExpenseCategory(str, Enum):
    ADMINISTRATIVE = "ADMINISTRATIVE"
    MAINTENANCE = "MAINTENANCE"
    UTILITIES = "UTILITIES"
    SALARY = "SALARY"
    TAX = "TAX"
    LEGAL = "LEGAL"
    CONSTRUCTION = "CONSTRUCTION"
    OTHER = "OTHER"


class ProjectStatus(str, Enum):
    PLANNING = "PLANNING"
    UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION"
    OPERATIONAL = "OPERATIONAL"
    COMPLETED = "COMPLETED"
    SUSPENDED = "SUSPENDED"


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    TREASURER = "TREASURER"
    VIEWER = "VIEWER"


class ConfigValueType(str, Enum):
    DECIMAL = "DECIMAL"
    INTEGER = "INTEGER"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"


class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    VERIFY = "VERIFY"
    REVERSE = "REVERSE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    EXIT = "EXIT"
    DEACTIVATE = "DEACTIVATE"
    LOGIN = "LOGIN"
    CONFIG_CHANGE = "CONFIG_CHANGE"
