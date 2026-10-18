# Cooperative Financial Management ERP — API Contract Specification

> **Document Status**: Authoritative REST API Contract  
> **API Version**: `/api/v1`  
> **Milestone**: Chapter 02 — Repair the Foundations  

---

## 1. Authentication & Security Architecture

### 1.1 Bearer Token
All protected endpoints require an HTTP `Authorization` header:
```http
Authorization: Bearer <jwt_access_token>
```

### 1.2 Role-Based Access Control (RBAC) Matrix

| Endpoint Group | Method & Route | ADMIN | TREASURER | VIEWER |
|---|---|:---:|:---:|:---:|
| **Auth** | `POST /api/v1/auth/login` | Public | Public | Public |
| | `GET /api/v1/auth/me` | ✅ | ✅ | ✅ |
| | `POST /api/v1/auth/change-password` | ✅ | ✅ | ✅ |
| **Members** | `GET /api/v1/members` | ✅ | ✅ | ✅ |
| | `POST /api/v1/members` | ✅ | ✅ | ❌ |
| | `GET /api/v1/members/{id}` | ✅ | ✅ | ✅ |
| | `PUT /api/v1/members/{id}` | ✅ | ✅ | ❌ |
| | `POST /api/v1/members/{id}/exit` | ✅ | ❌ | ❌ |
| | `GET /api/v1/members/{id}/statement` | ✅ | ✅ | ✅ |
| **Contributions** | `GET /api/v1/contributions` | ✅ | ✅ | ✅ |
| | `POST /api/v1/contributions` | ✅ | ✅ | ❌ |
| | `POST /api/v1/contributions/{id}/verify` | ✅ | ✅ | ❌ |
| | `POST /api/v1/contributions/{id}/reverse` | ✅ | ❌ | ❌ |
| **Withdrawals** | `GET /api/v1/withdrawals` | ✅ | ✅ | ✅ |
| | `POST /api/v1/withdrawals` | ✅ | ✅ | ❌ |
| | `POST /api/v1/withdrawals/{id}/approve` | ✅ | ❌ | ❌ |
| | `POST /api/v1/withdrawals/{id}/reject` | ✅ | ❌ | ❌ |
| | `POST /api/v1/withdrawals/{id}/mark-paid` | ✅ | ✅ | ❌ |
| **Funds** | `GET /api/v1/funds` | ✅ | ✅ | ✅ |
| | `GET /api/v1/funds/{id}` | ✅ | ✅ | ✅ |
| | `GET /api/v1/funds/{id}/transactions` | ✅ | ✅ | ✅ |
| | `POST /api/v1/funds/transfers` | ✅ | ✅ | ❌ |
| | `GET /api/v1/funds/{id}/reconciliation` | ✅ | ✅ | ❌ |
| **Transactions** | `GET /api/v1/transactions` (Read-only) | ✅ | ✅ | ✅ |
| | `GET /api/v1/transactions/{id}` | ✅ | ✅ | ✅ |
| **Projects** | `GET /api/v1/projects` | ✅ | ✅ | ✅ |
| | `POST /api/v1/projects` | ✅ | ❌ | ❌ |
| | `GET /api/v1/projects/{id}` | ✅ | ✅ | ✅ |
| | `PUT /api/v1/projects/{id}` | ✅ | ❌ | ❌ |
| **Properties** | `GET /api/v1/properties` | ✅ | ✅ | ✅ |
| | `POST /api/v1/properties` | ✅ | ❌ | ❌ |
| | `GET /api/v1/properties/{id}` | ✅ | ✅ | ✅ |
| | `POST /api/v1/properties/{id}/units` | ✅ | ❌ | ❌ |
| | `POST /api/v1/properties/rental-income` | ✅ | ✅ | ❌ |
| **Expenses** | `GET /api/v1/expenses` | ✅ | ✅ | ✅ |
| | `POST /api/v1/expenses` | ✅ | ✅ | ❌ |
| **Configuration** | `GET /api/v1/config` | ✅ | ✅ | ✅ |
| | `PUT /api/v1/config/{key}` | ✅ | ❌ | ❌ |
| | `GET /api/v1/config/{key}/history` | ✅ | ❌ | ❌ |
| **Reports** | `GET /api/v1/reports/dashboard` | ✅ | ✅ | ✅ |
| | `GET /api/v1/reports/trial-balance` | ✅ | ✅ | ✅ |
| | `GET /api/v1/reports/member-compliance` | ✅ | ✅ | ✅ |
| | `GET /api/v1/reports/income-statement` | ✅ | ✅ | ✅ |

---

## 2. Standard Envelope & Error Codes

### 2.1 Generic Paginated Result
All collection endpoints support pagination via query parameters: `?page=1&per_page=25`.
Response structure:
```json
{
  "items": [],
  "total": 150,
  "page": 1,
  "per_page": 25,
  "pages": 6
}
```

### 2.2 Error Mapping
Domain exceptions are intercepted and translated to HTTP error envelopes:
```json
{
  "detail": {
    "message": "Human readable error description",
    "error_code": "INSUFFICIENT_FUNDS",
    "field_errors": {}
  }
}
```

| Exception | HTTP Status | Error Code |
|---|---|---|
| `NotFoundError` | 404 Not Found | `NOT_FOUND` |
| `BusinessValidationError` | 400 Bad Request / 422 Unprocessable | `VALIDATION_ERROR` |
| `AuthorizationError` | 403 Forbidden | `FORBIDDEN` |
| `ImmutabilityError` | 422 Unprocessable Entity | `IMMUTABILITY_ERROR` |
| `InsufficientFundsError` | 422 Unprocessable Entity | `INSUFFICIENT_FUNDS` |
| `InvalidStateTransitionError` | 422 Unprocessable Entity | `INVALID_STATE_TRANSITION` |
| `DuplicateError` | 409 Conflict | `DUPLICATE` |

---

## 3. Endpoints by Domain

### 3.1 Authentication
- **`POST /api/v1/auth/login`**
  - Body: `LoginRequest { username: str, password: str }`
  - Response (200): `LoginResponse { access_token: str, token_type: "bearer", expires_in: int, user: UserResponse }`
- **`GET /api/v1/auth/me`**
  - Response (200): `UserResponse { id: UUID, username: str, email: str, full_name: str, role: UserRole, is_active: bool }`
- **`POST /api/v1/auth/change-password`**
  - Body: `{ old_password: str, new_password: str }`
  - Response (200): `{ message: "Password updated successfully" }`

### 3.2 Members
- **`GET /api/v1/members`**
  - Query: `page: int, per_page: int, status: MemberStatus | None, search: str | None`
  - Response (200): `PaginatedResult<MemberSummary>`
- **`POST /api/v1/members`**
  - Body: `MemberCreate { member_number: str, full_name: str, phone: str, email: str | None, address: str | None, date_joined: date }`
  - Response (201): `MemberDetail`
- **`GET /api/v1/members/{id}`**
  - Response (200): `MemberDetail { id, member_number, full_name, phone, email, address, status, shares: ShareSummary, total_contributed: Decimal }`
- **`PUT /api/v1/members/{id}`**
  - Body: `MemberUpdate { full_name: str | None, phone: str | None, email: str | None, address: str | None, notes: str | None }`
  - Response (200): `MemberDetail`
- **`POST /api/v1/members/{id}/exit`**
  - Body: `MemberExitRequest { exit_date: date, exit_reason: str, notes: str | None }`
  - Response (200): `MemberDetail`
- **`GET /api/v1/members/{id}/statement`**
  - Query: `from_date: date | None, to_date: date | None`
  - Response (200): `MemberStatement { member: MemberSummary, contributions: list, withdrawals: list, net_balance: Decimal }`

### 3.3 Contributions
- **`GET /api/v1/contributions`**
  - Query: `page, per_page, status, member_id, from_date, to_date`
  - Response (200): `PaginatedResult<ContributionResponse>`
- **`POST /api/v1/contributions`**
  - Body: `ContributionCreate { member_id: UUID, contribution_date: date, member_amount: Decimal, operating_amount: Decimal, bank_reference: str, period_label: str | None, notes: str | None }`
  - Response (201): `ContributionResponse`
  - *Side Effect*: Atomically inserts two ledger entries (MEMBER_CONTRIBUTION into MEMBER_EQUITY fund, OPERATING_CONTRIBUTION into OPERATING fund).
- **`POST /api/v1/contributions/{id}/verify`**
  - Body: `{ notes: str | None }`
  - Response (200): `ContributionResponse`
- **`POST /api/v1/contributions/{id}/reverse`**
  - Body: `{ reason: str }`
  - Response (200): `ContributionResponse`
  - *Side Effect*: Inserts two reversing transactions in the ledger with `reversal_of` links.

### 3.4 Withdrawals
- **`GET /api/v1/withdrawals`**
  - Query: `page, per_page, status, withdrawal_type, member_id`
  - Response (200): `PaginatedResult<WithdrawalResponse>`
- **`POST /api/v1/withdrawals`**
  - Body: `WithdrawalCreate { member_id: UUID, withdrawal_type: WithdrawalType, amount: Decimal, requested_date: date, reason: str | None }`
  - Response (201): `WithdrawalResponse`
- **`POST /api/v1/withdrawals/{id}/approve`**
  - Response (200): `WithdrawalResponse`
- **`POST /api/v1/withdrawals/{id}/reject`**
  - Body: `{ reason: str }`
  - Response (200): `WithdrawalResponse`
- **`POST /api/v1/withdrawals/{id}/mark-paid`**
  - Body: `{ paid_date: date, bank_reference: str, notes: str | None }`
  - Response (200): `WithdrawalResponse`
  - *Side Effect*: Inserts DEBIT transaction on MEMBER_EQUITY fund. If EXIT_PAYOUT, transitions member status to EXITED.

### 3.5 Funds & Ledger
- **`GET /api/v1/funds`**
  - Response (200): `list<FundResponse>`
- **`GET /api/v1/funds/{id}`**
  - Response (200): `FundResponse`
- **`GET /api/v1/funds/{id}/transactions`**
  - Query: `page, per_page, from_date, to_date, transaction_type`
  - Response (200): `PaginatedResult<TransactionResponse>`
- **`POST /api/v1/funds/transfers`**
  - Body: `FundTransferCreate { source_fund_id: UUID, destination_fund_id: UUID, amount: Decimal, description: str, transfer_date: date }`
  - Response (201): `FundTransferResponse`
  - *Side Effect*: Inserts balanced pair of `FUND_TRANSFER_OUT` and `FUND_TRANSFER_IN` transactions.
- **`GET /api/v1/funds/{id}/reconciliation`**
  - Response (200): `ReconciliationResult { fund_id: UUID, current_balance: Decimal, calculated_balance: Decimal, is_reconciled: bool, transaction_count: int }`
- **`GET /api/v1/transactions`** (Strictly Read-Only)
  - Query: `page, per_page, fund_id, member_id, transaction_type, from_date, to_date`
  - Response (200): `PaginatedResult<TransactionResponse>`
- **`GET /api/v1/transactions/{id}`**
  - Response (200): `TransactionResponse`

### 3.6 Projects, Properties & Expenses
- **`GET /api/v1/projects`** → `list<ProjectResponse>`
- **`POST /api/v1/projects`** → `ProjectResponse` (201)
- **`GET /api/v1/properties`** → `list<PropertyResponse>`
- **`POST /api/v1/properties`** → `PropertyResponse` (201)
- **`POST /api/v1/properties/{id}/units`** → `RentalUnitResponse` (201)
- **`POST /api/v1/properties/rental-income`** → `RentalIncomeResponse` (201)
  - *Side Effect*: Inserts CREDIT transaction on RENTAL_INCOME fund.
- **`GET /api/v1/expenses`** → `PaginatedResult<ExpenseResponse>`
- **`POST /api/v1/expenses`** → `ExpenseResponse` (201)
  - *Side Effect*: Inserts DEBIT transaction on target fund (OPERATING or PROJECT).

### 3.7 Configuration
- **`GET /api/v1/config`** → `list<ConfigValue>`
- **`PUT /api/v1/config/{key}`**
  - Body: `ConfigUpdate { config_value: str, effective_from: date, description: str | None }`
  - Response (200): `ConfigValue`
- **`GET /api/v1/config/{key}/history`** → `list<ConfigHistory>`

### 3.8 Reports
- **`GET /api/v1/reports/dashboard`** → `DashboardMetrics`
- **`GET /api/v1/reports/trial-balance`** → `TrialBalanceReport`
- **`GET /api/v1/reports/member-compliance`** → `MemberComplianceReport`
- **`GET /api/v1/reports/income-statement`** → `IncomeStatementReport`
