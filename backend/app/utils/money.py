"""
Currency/monetary utility functions.

RULES FOR MONETARY VALUES:
1. All monetary values in the system use Python Decimal, NEVER float.
2. All monetary values are stored as Numeric(15, 2) in PostgreSQL.
3. Rounding: ROUND_HALF_UP to 2 decimal places.
4. Display format: Always show 2 decimal places (e.g., "5000.00").
5. Currency: ETB (single currency for v1).

IMPLEMENTATION NOTE FOR GEMINI:
Implement helpers for:
  - parse_money(value: str | int | float | Decimal) -> Decimal
  - format_money(value: Decimal) -> str
  - validate_positive(value: Decimal, field_name: str) -> Decimal
"""

from decimal import Decimal, ROUND_HALF_UP

CURRENCY_CODE = "ETB"
MONEY_PRECISION = Decimal("0.01")


def round_money(value: Decimal) -> Decimal:
    """Round a monetary value to 2 decimal places using banker-friendly rounding."""
    return value.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)
