"""
Fund and FundTransfer Pydantic Schemas.

Module: Finance
See: api_contract.md → Funds

TODO (Gemini):
    - FundResponse: id, name, fund_type, description, current_balance, is_active
    - FundDetail: FundResponse + recent_transactions
    - FundTransferCreate: source_fund_id (UUID), destination_fund_id (UUID),
                          amount (Decimal), description (str), transfer_date (date)
    - FundTransferResponse: all fields + source_fund_name, destination_fund_name
    - ReconciliationResult: fund_id, fund_name, cached_balance, computed_balance,
                            discrepancy, is_reconciled (bool)
"""

# class FundResponse(BaseModel): ...
# class FundTransferCreate(BaseModel): ...
# class ReconciliationResult(BaseModel): ...
