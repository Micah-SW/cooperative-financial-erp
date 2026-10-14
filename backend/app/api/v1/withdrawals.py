"""
Withdrawals API Router.

Endpoints:
    GET    /                — List withdrawals (ALL roles)
    POST   /                — Create withdrawal (ADMIN, TREASURER)
    POST   /{id}/approve    — Approve withdrawal (ADMIN)
    POST   /{id}/reject     — Reject withdrawal (ADMIN)
    POST   /{id}/mark-paid  — Mark as paid (ADMIN, TREASURER)

See: api_contract.md → Withdrawals
Depends: WithdrawalService
"""

# router = APIRouter()
# TODO (Gemini): Implement endpoints
