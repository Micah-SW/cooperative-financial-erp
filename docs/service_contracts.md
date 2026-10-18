# Cooperative Financial Management ERP — Service Contracts Specification

> **Document Status**: Authoritative Business Logic & Service Contract Specification  
> **Milestone**: Chapter 02 — Repair the Foundations  

---

## 1. Architectural Invariants for Services

1. **Transaction Boundary Ownership**:
   - Every service method accepts `db: AsyncSession` as its first parameter.
   - Services MUST NOT execute `await db.commit()` independently. The transaction boundary is owned by the API route handler or FastAPI dependency wrapper.
   - If an error is encountered, the service raises a domain exception; the caller initiates rollback.

2. **Audit Logging Mandate**:
   - Any service method mutating persistent state MUST invoke `AuditService.log()` within the caller's transaction.
   - No financial mutation may complete without an accompanying audit record.

3. **Financial Ledger Invariance**:
   - Financial ledger records (`Transaction`) are created exclusively via `TransactionService.create_transaction()`. No other service may construct or insert `Transaction` model instances directly.
   - Direct updates or deletions on transactions are strictly prohibited.

---

## 2. Core Services

### 2.1 `AuthService` (`backend/app/services/auth_service.py`)
- **`authenticate(db: AsyncSession, username: str, password: str) -> User`**
  - Verifies user exists, `is_active == True`, and bcrypt hash matches.
  - Updates `last_login = now()`.
  - Raises `AuthorizationError` on bad credentials or inactive account.
- **`change_password(db: AsyncSession, user_id: UUID, old_pw: str, new_pw: str) -> None`**
  - Verifies old password. Updates password hash. Emits `AuditAction.CONFIG_CHANGE`.
- **`get_user_by_id(db: AsyncSession, user_id: UUID) -> User`**
  - Returns `User` or raises `NotFoundError`.

### 2.2 `AuditService` (`backend/app/core/audit.py`)
- **`log(db: AsyncSession, *, user_id: UUID, action: AuditAction, entity_type: str, entity_id: UUID, old_values: dict | None = None, new_values: dict | None = None, ip_address: str | None = None) -> AuditLog`**
  - Inserts `AuditLog` entry in current transaction.
- **`list_logs(db: AsyncSession, *, filters: dict, page: int = 1, per_page: int = 25) -> PaginatedResult[AuditLog]`**
  - Paginated query filtered by `user_id`, `entity_type`, date range. ADMIN only.

### 2.3 `ConfigService` (`backend/app/services/config_service.py`)
- **`get(db: AsyncSession, key: str, as_of: date | None = None) -> SystemConfig`**
  - Fetches currently effective config (where `effective_to IS NULL`) or historically effective record.
  - Raises `NotFoundError` if missing.
- **`set(db: AsyncSession, key: str, value: str, user_id: UUID, effective_from: date | None = None) -> SystemConfig`**
  - Closes active record (`effective_to = new_from - 1 day`). Inserts new record.
  - Emits `AuditAction.CONFIG_CHANGE`.
- **`get_history(db: AsyncSession, key: str) -> list[SystemConfig]`**
  - Returns all historical versions of a key ordered by `effective_from DESC`.

---

## 3. Member Domain Services

### 3.1 `MemberService` (`backend/app/services/member_service.py`)
- **`create_member(db: AsyncSession, data: MemberCreate, user_id: UUID) -> Member`**
  - Enforces `MEMBERSHIP_OPEN` config flag (raises `BusinessValidationError` if closed).
  - Checks uniqueness of `member_number`.
  - Creates initial 12 shares based on effective `SHARE_VALUE` config.
  - Emits `AuditAction.CREATE`.
- **`update_member(db: AsyncSession, member_id: UUID, data: MemberUpdate, user_id: UUID) -> Member`**
  - Updates contact info (phone, email, address, notes). `member_number` is immutable.
  - Emits `AuditAction.UPDATE`.
- **`get_member(db: AsyncSession, member_id: UUID) -> Member`**
  - Returns member with associated shares and recent history.
- **`list_members(db: AsyncSession, filters: dict, page: int = 1, per_page: int = 25) -> PaginatedResult[Member]`**
- **`exit_member(db: AsyncSession, member_id: UUID, exit_data: MemberExitRequest, user_id: UUID) -> Member`**
  - Verifies member is currently `ACTIVE`.
  - Sets `status = EXITED`, `date_exited = exit_data.exit_date`, `exit_reason`.
  - Appends final `Share` record with `share_count = 0`.
  - Emits `AuditAction.EXIT`.
  - **Classification Note (UBR-1 & UBR-17)**: Members have the confirmed right to leave the cooperative, receive refundable money under applicable rules, have shares extinguished, and retain permanent historical records (**Confirmed Business Requirement**). The software enforces `ACTIVE` → `EXITED` as an irreversible transition in v1 without deletion (**Proposed Technical Safeguard**). Whether an exited member could later be readmitted if membership reopens is an **Unresolved Business Decision**. Payout calculation and shared loss deduction rules are also **Unresolved Business Decisions**; payout amounts must be entered manually by authorized administrators rather than calculated by unapproved formulas.

---

## 4. Financial & Ledger Services

### 4.1 `TransactionService` (`backend/app/services/transaction_service.py`) — Internal Core
- **`create_transaction(db: AsyncSession, *, fund_id: UUID, transaction_type: TransactionType, amount: Decimal, direction: TransactionDirection, reference_type: str, reference_id: UUID, user_id: UUID, member_id: UUID | None = None, description: str = "", transaction_date: date | None = None) -> Transaction`**
  - Locks `Fund` row with `FOR UPDATE`.
  - Validates `amount > 0`.
  - Calculates new `balance_after = current_balance +/- amount`.
  - If DEBIT and balance would go negative without override, raises `InsufficientFundsError`.
  - Updates `fund.current_balance`.
  - Inserts immutable `Transaction` record.
  - Emits `AuditAction.CREATE`.
- **`reverse_transaction(db: AsyncSession, *, transaction_id: UUID, reason: str, user_id: UUID) -> Transaction`**
  - Validates target transaction has not already been reversed.
  - Creates reversing transaction with opposite direction and `reversal_of = transaction_id`.
  - Updates fund balance accordingly.

### 4.2 `ContributionService` (`backend/app/services/contribution_service.py`)
- **`record_contribution(db: AsyncSession, data: ContributionCreate, user_id: UUID) -> Contribution`**
  - Validates member is `ACTIVE`.
  - Validates amounts: `total = member_amount + operating_amount`.
  - Inserts `Contribution` record in `RECORDED` status.
  - Creates `MEMBER_CONTRIBUTION` credit transaction in `MEMBER_EQUITY` fund.
  - Creates `OPERATING_CONTRIBUTION` credit transaction in `OPERATING` fund.
  - Emits `AuditAction.CREATE`.
- **`verify_contribution(db: AsyncSession, contribution_id: UUID, user_id: UUID, notes: str | None = None) -> Contribution`**
  - Transitions status from `RECORDED` → `VERIFIED`. Sets `verified_by`, `verified_at`.
  - Emits `AuditAction.VERIFY`.
  - **Classification Note (UBR-9 & UBR-16)**: Members deposit directly into cooperative bank accounts (**Confirmed Business Requirement**). The formal multi-tier approval workflow and resolution window for unreferenced deposits are **Unresolved Business Decisions**. Requiring manual entry of the bank reference slip before marking `VERIFIED` is a **Proposed Technical Safeguard**.
- **`reverse_contribution(db: AsyncSession, contribution_id: UUID, reason: str, user_id: UUID) -> Contribution`**
  - Transitions status to `DISPUTED`.
  - Calls `transaction_service.reverse_transaction()` for both associated ledger transactions.
  - Emits `AuditAction.REVERSE`.

### 4.3 `WithdrawalService` (`backend/app/services/withdrawal_service.py`)
- **`request_withdrawal(db: AsyncSession, data: WithdrawalCreate, user_id: UUID) -> Withdrawal`**
  - If `withdrawal_type == PARTIAL_WITHDRAWAL`, checks `PARTIAL_WITHDRAWAL_ALLOWED` config (UBR-8).
  - Inserts `Withdrawal` in `PENDING` status. No ledger transactions created at request time.
- **`approve_withdrawal(db: AsyncSession, withdrawal_id: UUID, user_id: UUID) -> Withdrawal`**
  - Transitions `PENDING` → `APPROVED`. Emits `AuditAction.APPROVE`.
- **`reject_withdrawal(db: AsyncSession, withdrawal_id: UUID, reason: str, user_id: UUID) -> Withdrawal`**
  - Transitions `PENDING` → `REJECTED`. Emits `AuditAction.REJECT`.
- **`mark_paid(db: AsyncSession, withdrawal_id: UUID, payment_data: dict, user_id: UUID) -> Withdrawal`**
  - Transitions `APPROVED` → `PAID`.
  - Creates `WITHDRAWAL` debit transaction in `MEMBER_EQUITY` fund.
  - If `EXIT_PAYOUT`, calls `member_service.exit_member()`.
  - Emits `AuditAction.UPDATE`.

### 4.4 `FundService` (`backend/app/services/fund_service.py`)
- **`transfer(db: AsyncSession, source_id: UUID, dest_id: UUID, amount: Decimal, description: str, user_id: UUID) -> FundTransfer`**
  - Validates `source_id != dest_id` and `amount > 0`.
  - Inserts `FundTransfer` record.
  - Creates `FUND_TRANSFER_OUT` debit transaction from source fund.
  - Creates `FUND_TRANSFER_IN` credit transaction to destination fund.
  - Emits `AuditAction.CREATE`.
- **`reconcile_fund(db: AsyncSession, fund_id: UUID) -> ReconciliationResult`**
  - Computes `sum = SUM(amount * direction_sign)` from `Transaction` table.
  - Compares against `fund.current_balance`. Reports discrepancies.

---

## 5. Operations, Asset & Reporting Services

### 5.1 `ProjectService` (`backend/app/services/project_service.py`)
- **`create_project(db: AsyncSession, data: ProjectCreate, user_id: UUID) -> Project`**
- **`update_project(db: AsyncSession, project_id: UUID, data: ProjectUpdate, user_id: UUID) -> Project`**

### 5.2 `PropertyService` (`backend/app/services/property_service.py`)
- **`create_property(db: AsyncSession, data: PropertyCreate, user_id: UUID) -> Property`**
- **`add_rental_unit(db: AsyncSession, property_id: UUID, data: RentalUnitCreate, user_id: UUID) -> RentalUnit`**
- **`record_rental_income(db: AsyncSession, data: RentalIncomeCreate, user_id: UUID) -> RentalIncome`**
  - Inserts `RentalIncome` record.
  - Creates `RENTAL_INCOME` credit transaction in `RENTAL_INCOME` fund.
  - Emits `AuditAction.CREATE`.
  - **Classification Note (UBR-18)**: Investment profits do not belong to individual members. Cooperative income supports normal union expenses, and remaining rental-project income is intended for the mall project (**Confirmed Business Requirement**). Rental income credits dedicated cooperative funds; zero dividends are paid to members. The exact allocation split between union expenses and the mall project, and whether a statutory reserve is required, are **Unresolved Business Decisions**.

### 5.3 `ExpenseService` (`backend/app/services/expense_service.py`)
- **`record_expense(db: AsyncSession, data: ExpenseCreate, user_id: UUID) -> Expense`**
  - Inserts `Expense` record.
  - Creates `EXPENSE` debit transaction in target fund.
  - If linked to a `project_id`, increments `project.spent`.
  - Emits `AuditAction.CREATE`.

### 5.4 `ReportService` (`backend/app/services/report_service.py`)
- **`get_dashboard_metrics(db: AsyncSession) -> DashboardMetrics`**
  - Aggregates active members, fund balances, monthly income vs expense.
- **`get_trial_balance(db: AsyncSession) -> TrialBalanceReport`**
  - Verified equality of ledger debits and credits across all funds.
- **`get_member_statement(db: AsyncSession, member_id: UUID, start_date: date | None, end_date: date | None) -> MemberStatement`**
  - Returns itemized contributions, share value, and transaction history.
