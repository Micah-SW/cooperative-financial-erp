"""
Withdrawal Pydantic Schemas.

Module: Finance
See: api_contract.md → Withdrawals

TODO (Gemini):
    - WithdrawalCreate: member_id (UUID), withdrawal_type (WithdrawalType),
                        amount (Decimal), reason?, notes?
    - WithdrawalApprove: (empty body or notes)
    - WithdrawalReject: reason (str)
    - WithdrawalMarkPaid: paid_date (date), bank_reference?
    - WithdrawalResponse: all fields + member_name, approver_name
"""

# class WithdrawalCreate(BaseModel): ...
# class WithdrawalMarkPaid(BaseModel): ...
# class WithdrawalResponse(BaseModel): ...
