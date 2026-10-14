"""
Member Pydantic Schemas.

Module: Member
See: api_contract.md → Members

TODO (Gemini):
    - MemberCreate: member_number, full_name, phone?, email?, address?,
                    date_joined, initial_share_count (int), notes?
    - MemberUpdate: full_name?, phone?, email?, address?, notes?
                    (member_number and status are NOT updatable)
    - MemberExit: exit_date, exit_reason, payout_amount (Decimal)
    - MemberSummary: id, member_number, full_name, phone, status, date_joined,
                     current_share_count, current_share_value, accumulated_balance
    - MemberDetail: all of MemberSummary + email, address, date_exited, exit_reason,
                    notes, shares (list), recent_contributions (list)
    - All monetary fields: Decimal, serialized as string with 2 decimal places
"""

# class MemberCreate(BaseModel): ...
# class MemberUpdate(BaseModel): ...
# class MemberExit(BaseModel): ...
# class MemberSummary(BaseModel): ...
# class MemberDetail(BaseModel): ...
