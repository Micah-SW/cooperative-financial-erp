"""
Expense ORM Model.

Entity: Expense
Schema: coop.expenses
Module: Expense

See: database_schema.md → coop.expenses
See: domain_model.md → Expense

Business Rules:
    - Recording creates DEBIT transaction on specified fund
    - Expenses reduce fund balance
    - Categories: ADMINISTRATIVE, MAINTENANCE, UTILITIES, SALARY, TAX, LEGAL, CONSTRUCTION, OTHER
    - Can be optionally linked to a project

TODO (Gemini):
    - Fields: id, fund_id (FK→funds), category (ExpenseCategory), description,
              amount, expense_date, vendor, receipt_reference, project_id (FK→projects, nullable),
              notes, created_at, created_by (FK→users)
    - CHECK: amount > 0
    - Indexes: fund_id, category, expense_date, project_id (partial)
"""

# class Expense(CoopBase):
#     __tablename__ = "expenses"
#     __table_args__ = {"schema": "coop"}
#     ...
