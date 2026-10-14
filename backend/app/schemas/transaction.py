"""
Transaction Pydantic Schemas.

Module: Finance
See: api_contract.md → Transactions

NOTE: Transactions are READ-ONLY via API. No create/update schemas.

TODO (Gemini):
    - TransactionResponse: id, fund_id, fund_name, transaction_type, amount,
                           direction, balance_after, member_id, member_name,
                           reference_type, reference_id, reversal_of,
                           description, transaction_date, created_at, created_by_name
    - TransactionFilters: fund_id?, member_id?, type?, from_date?, to_date?
"""

# class TransactionResponse(BaseModel): ...
# class TransactionFilters(BaseModel): ...
