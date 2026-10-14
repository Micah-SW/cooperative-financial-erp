"""
Contribution Pydantic Schemas.

Module: Finance
See: api_contract.md → Contributions

TODO (Gemini):
    - ContributionCreate: member_id (UUID), contribution_date (date),
                          member_amount (Decimal), operating_amount (Decimal),
                          bank_reference?, period_label?, notes?
        Validation: total = member_amount + operating_amount
    - ContributionVerify: bank_reference?, notes?
    - ContributionReverse: reason (str)
    - ContributionResponse: all fields + computed total_amount, member_name
    - ContributionSummary: aggregated view for reports
"""

# class ContributionCreate(BaseModel): ...
# class ContributionVerify(BaseModel): ...
# class ContributionReverse(BaseModel): ...
# class ContributionResponse(BaseModel): ...
