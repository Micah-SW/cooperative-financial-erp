"""
Expense Pydantic Schemas.

Module: Expense
See: api_contract.md → Expenses

TODO (Gemini):
    - ExpenseCreate: fund_id (UUID), category (ExpenseCategory), description (str),
                     amount (Decimal), expense_date (date), vendor?, receipt_reference?,
                     project_id? (UUID), notes?
    - ExpenseResponse: all fields + fund_name, project_name, created_by_name
    - ExpenseFilters: fund_id?, category?, from_date?, to_date?, project_id?
"""

# class ExpenseCreate(BaseModel): ...
# class ExpenseResponse(BaseModel): ...
