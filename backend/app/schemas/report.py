"""
Report Pydantic Schemas.

Module: Reporting
See: api_contract.md → Reports

TODO (Gemini):
    - MemberBalanceReport: member_id, member_number, full_name, status,
                           accumulated_balance, share_value
    - ContributionSummaryReport: period, total_collected, member_count,
                                 members (list of per-member totals)
    - FundSummaryReport: fund_id, fund_name, opening_balance, total_credits,
                         total_debits, closing_balance, net_change
    - RentalIncomeSummaryReport: property_name, unit_identifier, total_income,
                                  payment_count
    - ExpenseSummaryReport: category, total_amount, expense_count
    - MemberStatement: member_id, member_name, period, opening_balance,
                       transactions (list with running balance), closing_balance
    - DashboardMetrics: total_members, active_members, total_member_equity,
                        total_contributions_this_month, fund_balances (list)
"""

# class MemberBalanceReport(BaseModel): ...
# class ContributionSummaryReport(BaseModel): ...
# class FundSummaryReport(BaseModel): ...
# class MemberStatement(BaseModel): ...
# class DashboardMetrics(BaseModel): ...
