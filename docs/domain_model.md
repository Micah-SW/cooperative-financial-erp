# Cooperative Financial Management ERP — Domain Model Specification

> **Document Status**: Authoritative Specification — Reconstructed from Repository Architecture  
> **Milestone**: Chapter 02 — Repair the Foundations  
> **Schema Scope**: `coop` PostgreSQL Schema  

---

## 1. Domain Overview

The Cooperative Financial Management ERP is designed to administer financial operations, equity ownership, recurring contributions, asset management, and expenditure tracking for a closed cooperative of approximately 150 members in Ethiopia (operating in Ethiopian Birr — ETB).

### Core Principles
1. **Immutable Ledger**: Financial transactions and audit logs are append-only. No physical UPDATE or DELETE operations are permitted on ledger records.
2. **Double-Entry Fund Tracking**: Every monetary movement creates paired or balanced credit/debit transaction records across dedicated cooperative funds.
3. **Strict Separation of Member vs. Cooperative Assets**: Investment profits, rental earnings, and union operating assets belong exclusively to the cooperative entity and are never merged into individual member balances (UBR-3). Cooperative income supports normal union operating expenses, and the remaining rental-project income is intended for the mall project (UBR-18).
4. **Effective Dating for Configuration**: Configurable thresholds (nominal share value, contribution amounts) are effective-dated to preserve historical accounting fidelity.
5. **Business Rule Classification**: All domain specifications distinguish Confirmed Cooperative Requirements, Unresolved Business Decisions, and Proposed Technical Safeguards (see [`docs/OPEN_QUESTIONS.md`](file:///c:/Users/Cyberpunk/Documents/mom_company_erp/docs/OPEN_QUESTIONS.md)).

---

## 2. Canonical Enumerations

All enumerations are defined in [`backend/app/core/enums.py`](file:///C:/Users/Cyberpunk/Documents/mom_company_erp/backend/app/core/enums.py) and serve as the single source of truth across backend models, Pydantic schemas, and frontend TypeScript definitions.

| Enum | Values | Description |
|---|---|---|
| `MemberStatus` | `ACTIVE`, `EXITED`, `SUSPENDED` | Lifecycle state of a member. The one-way transition `ACTIVE` → `EXITED` in v1 is a **technical safeguard** to prevent accidental reactivation and preserve audit history. Whether readmission is permitted under cooperative bylaws is an **unresolved business decision** (UBR-17). `SUSPENDED` reserved per UBR-11. |
| `TransactionType` | `MEMBER_CONTRIBUTION`, `OPERATING_CONTRIBUTION`, `WITHDRAWAL`, `EXIT_PAYOUT`, `RENTAL_INCOME`, `EXPENSE`, `FUND_TRANSFER_IN`, `FUND_TRANSFER_OUT`, `CORRECTION`, `REVERSAL`, `OPENING_BALANCE` | Ledger transaction classifications. |
| `TransactionDirection` | `CREDIT`, `DEBIT` | Direction of balance movement for a fund. |
| `FundType` | `MEMBER_EQUITY`, `OPERATING`, `PROJECT`, `RENTAL_INCOME`, `RESERVE` | Cooperative fund categories. `RESERVE` is a schema placeholder; statutory reserve necessity and rental income allocation formulas are **unresolved business decisions** (UBR-18). |
| `ContributionStatus` | `RECORDED`, `VERIFIED`, `DISPUTED` | Verification flow for direct member bank deposits. Manual verification by treasurer is a **technical safeguard**; formal approval process is an **unresolved business decision** (UBR-9, UBR-16). |
| `WithdrawalStatus` | `PENDING`, `APPROVED`, `PAID`, `REJECTED` | Approval and settlement flow for withdrawals. |
| `WithdrawalType` | `EXIT_PAYOUT`, `PARTIAL_WITHDRAWAL` | Payout reason. `PARTIAL_WITHDRAWAL` disabled by default (**technical safeguard**) pending cooperative policy (**unresolved business decision**, UBR-8). |
| `ExpenseCategory` | `ADMINISTRATIVE`, `MAINTENANCE`, `UTILITIES`, `SALARY`, `TAX`, `LEGAL`, `CONSTRUCTION`, `OTHER` | Cooperative union expenditure categories. |
| `ProjectStatus` | `PLANNING`, `UNDER_CONSTRUCTION`, `OPERATIONAL`, `COMPLETED`, `SUSPENDED` | Lifecycle status of investment capital projects. |
| `UserRole` | `ADMIN`, `TREASURER`, `VIEWER` | Role-based authorization levels for system users. |
| `ConfigValueType` | `DECIMAL`, `INTEGER`, `STRING`, `BOOLEAN` | Data types supported by effective-dated system config. |
| `AuditAction` | `CREATE`, `UPDATE`, `VERIFY`, `REVERSE`, `APPROVE`, `REJECT`, `EXIT`, `DEACTIVATE`, `LOGIN`, `CONFIG_CHANGE` | Sensitive mutation events recorded in the audit trail. |

---

## 3. Entity Specifications

### 3.1 Common Base (`CoopBase`)
- **`id`**: `UUID` — Primary key, defaults to `gen_random_uuid()`
- **`created_at`**: `TIMESTAMPTZ` — Audit timestamp, server default `now()`
- **Target Schema**: `coop`

### 3.2 Identity & Access

#### `User`
- **Table**: `coop.users`
- **Fields**:
  - `id`: UUID (PK)
  - `username`: VARCHAR(50) — Unique login identifier
  - `email`: VARCHAR(255) — Unique contact email
  - `hashed_password`: VARCHAR(255) — bcrypt hash
  - `full_name`: VARCHAR(100) — Display name
  - `role`: `UserRole` — ADMIN, TREASURER, or VIEWER
  - `is_active`: BOOLEAN — Default `true`
  - `last_login`: TIMESTAMPTZ (nullable)
  - `created_at`: TIMESTAMPTZ

#### `AuditLog`
- **Table**: `coop.audit_log`
- **Fields**:
  - `id`: UUID (PK)
  - `user_id`: UUID (FK → `coop.users.id`) — Actor
  - `action`: `AuditAction` — What operation was performed
  - `entity_type`: VARCHAR(50) — Target entity name (e.g., `Member`, `Contribution`)
  - `entity_id`: UUID — Identifier of affected entity
  - `old_values`: JSONB (nullable) — State prior to mutation
  - `new_values`: JSONB (nullable) — State after mutation
  - `ip_address`: VARCHAR(45) (nullable) — Client IP
  - `created_at`: TIMESTAMPTZ — Event timestamp (immutable)

#### `SystemConfig`
- **Table**: `coop.system_config`
- **Fields**:
  - `id`: UUID (PK)
  - `config_key`: VARCHAR(50) — e.g., `SHARE_VALUE`, `MEMBER_CONTRIBUTION_AMOUNT`
  - `config_value`: TEXT — Serialized value
  - `value_type`: `ConfigValueType` — DECIMAL, INTEGER, STRING, BOOLEAN
  - `description`: VARCHAR(255) — Rationale
  - `effective_from`: DATE — Start of effective window
  - `effective_to`: DATE (nullable) — End of effective window (`NULL` indicates currently active)
  - `created_at`: TIMESTAMPTZ
  - `created_by`: UUID (FK → `coop.users.id`)

---

### 3.3 Member & Equity Domain

#### `Member`
- **Table**: `coop.members`
- **Fields**:
  - `id`: UUID (PK)
  - `member_number`: VARCHAR(20) — Unique, immutable business identifier
  - `full_name`: VARCHAR(100) — Legal name
  - `phone`: VARCHAR(20) — Primary phone contact
  - `email`: VARCHAR(255) (nullable)
  - `address`: TEXT (nullable)
  - `date_joined`: DATE — Enrollment date
  - `date_exited`: DATE (nullable) — Exit date
  - `status`: `MemberStatus` — ACTIVE, EXITED, SUSPENDED
  - `exit_reason`: TEXT (nullable)
  - `notes`: TEXT (nullable)
  - `created_at`: TIMESTAMPTZ
  - `updated_at`: TIMESTAMPTZ (nullable)
  - `created_by`: UUID (FK → `coop.users.id`)

> **Classification Note (UBR-17)**: Members can leave the cooperative, receive their refundable money under applicable rules, have shares extinguished, and retain permanent historical records (**Confirmed Business Requirement**). The software enforces `ACTIVE` → `EXITED` as an irreversible transition in v1 without deletion (**Proposed Technical Safeguard**). Whether an exited member could later be readmitted if membership reopens is an **Unresolved Business Decision** and not a settled cooperative policy.

#### `Share`
- **Table**: `coop.shares`
- **Fields**:
  - `id`: UUID (PK)
  - `member_id`: UUID (FK → `coop.members.id`)
  - `share_count`: INTEGER — Number of shares held (currently 12)
  - `value_per_share`: NUMERIC(15, 2) — Nominal price per share (currently ETB 5,000.00)
  - `total_value`: NUMERIC(15, 2) — `share_count * value_per_share` (ETB 60,000.00)
  - `effective_date`: DATE — Date shares acquired or updated
  - `created_at`: TIMESTAMPTZ
  - `created_by`: UUID (FK → `coop.users.id`)

> **Classification Note (UBR-14)**: Each member currently holds 12 shares @ ETB 5,000 = ETB 60,000 (**Confirmed Business Requirement**). The accounting relationship between this initial ETB 60,000 share balance and subsequent recurring ETB 300 contributions is an **Unresolved Business Decision**. Storing shares and contributions in strictly separate tables without automated balance merging is a **Proposed Technical Safeguard**.

---

### 3.4 Financial Ledger & Funds Domain

#### `Fund`
- **Table**: `coop.funds`
- **Fields**:
  - `id`: UUID (PK)
  - `name`: VARCHAR(50) — Unique fund name
  - `fund_type`: `FundType` — MEMBER_EQUITY, OPERATING, PROJECT, RENTAL_INCOME, RESERVE
  - `description`: VARCHAR(255)
  - `current_balance`: NUMERIC(15, 2) — Denormalized cache of `SUM(transactions)`
  - `is_active`: BOOLEAN — Default `true`
  - `created_at`: TIMESTAMPTZ

> **Classification Note (UBR-18)**: Cooperative income supports normal union operating expenses, and remaining rental-project income is intended for the mall project; investment profits never belong to individual members (**Confirmed Business Requirement**). The precise allocation formula and whether a statutory Reserve Fund is mandated by bylaws are **Unresolved Business Decisions**. The `RESERVE` fund account is a **Proposed Technical Safeguard** schema placeholder.

#### `Transaction` (Immutable Ledger)
- **Table**: `coop.transactions`
- **Fields**:
  - `id`: UUID (PK)
  - `fund_id`: UUID (FK → `coop.funds.id`) — Fund whose balance changes
  - `transaction_type`: `TransactionType`
  - `amount`: NUMERIC(15, 2) — Strict CHECK `amount > 0`
  - `direction`: `TransactionDirection` — CREDIT or DEBIT
  - `balance_after`: NUMERIC(15, 2) — Running fund balance snapshot
  - `member_id`: UUID (FK → `coop.members.id`, nullable) — Associated member
  - `reference_type`: VARCHAR(50) — Source document type (`Contribution`, `Withdrawal`, etc.)
  - `reference_id`: UUID — Polymorphic identifier to source document
  - `reversal_of`: UUID (FK → `coop.transactions.id`, nullable) — Original transaction if reversal
  - `description`: VARCHAR(255)
  - `transaction_date`: DATE — Accounting date
  - `created_at`: TIMESTAMPTZ — Insertion timestamp
  - `created_by`: UUID (FK → `coop.users.id`)

#### `FundTransfer`
- **Table**: `coop.fund_transfers`
- **Fields**:
  - `id`: UUID (PK)
  - `source_fund_id`: UUID (FK → `coop.funds.id`)
  - `destination_fund_id`: UUID (FK → `coop.funds.id`)
  - `amount`: NUMERIC(15, 2) — CHECK `amount > 0`
  - `description`: VARCHAR(255)
  - `transfer_date`: DATE
  - `created_at`: TIMESTAMPTZ
  - `created_by`: UUID (FK → `coop.users.id`)

#### `Contribution`
- **Table**: `coop.contributions`
- **Fields**:
  - `id`: UUID (PK)
  - `member_id`: UUID (FK → `coop.members.id`)
  - `contribution_date`: DATE
  - `member_amount`: NUMERIC(15, 2) — Member equity portion (currently ETB 300.00)
  - `operating_amount`: NUMERIC(15, 2) — Union operating portion (currently ETB 50.00)
  - `total_amount`: NUMERIC(15, 2) — CHECK `total_amount = member_amount + operating_amount`
  - `bank_reference`: VARCHAR(100) — Bank transaction/slip code
  - `status`: `ContributionStatus` — RECORDED, VERIFIED, DISPUTED
  - `verified_by`: UUID (FK → `coop.users.id`, nullable)
  - `verified_at`: TIMESTAMPTZ (nullable)
  - `period_label`: VARCHAR(20) (nullable) — e.g. "2026-10"
  - `notes`: TEXT (nullable)
  - `created_at`: TIMESTAMPTZ
  - `created_by`: UUID (FK → `coop.users.id`)

> **Classification Note (UBR-9 & UBR-16)**: Members deposit directly into the cooperative's bank account, with current recurring amounts of ETB 300 member/project and ETB 50 union operating expenses (**Confirmed Business Requirement**). The formal verification workflow and handling of unreferenced bank inflows are **Unresolved Business Decisions**. Requiring manual entry of bank references by authorized staff prior to `VERIFIED` status is a **Proposed Technical Safeguard**.

#### `Withdrawal`
- **Table**: `coop.withdrawals`
- **Fields**:
  - `id`: UUID (PK)
  - `member_id`: UUID (FK → `coop.members.id`)
  - `withdrawal_type`: `WithdrawalType` — EXIT_PAYOUT, PARTIAL_WITHDRAWAL
  - `amount`: NUMERIC(15, 2) — Payout amount
  - `status`: `WithdrawalStatus` — PENDING, APPROVED, PAID, REJECTED
  - `requested_date`: DATE
  - `approved_by`: UUID (FK → `coop.users.id`, nullable)
  - `approved_at`: TIMESTAMPTZ (nullable)
  - `paid_date`: DATE (nullable)
  - `bank_reference`: VARCHAR(100) (nullable)
  - `reason`: TEXT (nullable)
  - `notes`: TEXT (nullable)
  - `created_at`: TIMESTAMPTZ
  - `created_by`: UUID (FK → `coop.users.id`)

> **Classification Note (UBR-1 & UBR-8)**: Members have the right to receive refundable money upon exit (**Confirmed Business Requirement**). The exact payout formula, deductions for shared project losses, waiting periods, and whether partial withdrawals are allowed are **Unresolved Business Decisions**. Gating partial withdrawals behind a config flag and deferring automated payout math are **Proposed Technical Safeguards**.

#### `BankAccount`
- **Table**: `coop.bank_accounts`
- **Fields**:
  - `id`: UUID (PK)
  - `bank_name`: VARCHAR(100) — e.g., Commercial Bank of Ethiopia (CBE)
  - `account_number`: VARCHAR(50) — Account number
  - `account_holder`: VARCHAR(100) — Cooperative legal title
  - `branch`: VARCHAR(100)
  - `is_active`: BOOLEAN — Default `true`
  - `created_at`: TIMESTAMPTZ

---

### 3.5 Projects, Assets & Operations Domain

#### `Project`
- **Table**: `coop.projects`
- **Fields**:
  - `id`: UUID (PK)
  - `name`: VARCHAR(100) — Project name
  - `description`: TEXT (nullable)
  - `status`: `ProjectStatus` — PLANNING, UNDER_CONSTRUCTION, OPERATIONAL, COMPLETED, SUSPENDED
  - `budget`: NUMERIC(15, 2)
  - `spent`: NUMERIC(15, 2) — Current expenditure total
  - `start_date`: DATE
  - `target_completion_date`: DATE (nullable)
  - `completion_date`: DATE (nullable)
  - `created_at`: TIMESTAMPTZ
  - `created_by`: UUID (FK → `coop.users.id`)

#### `Property`
- **Table**: `coop.properties`
- **Fields**:
  - `id`: UUID (PK)
  - `project_id`: UUID (FK → `coop.projects.id`, nullable)
  - `name`: VARCHAR(100) — Building / asset name
  - `property_type`: VARCHAR(50) — Commercial, residential, warehouse
  - `address`: TEXT
  - `acquisition_cost`: NUMERIC(15, 2)
  - `acquisition_date`: DATE
  - `current_valuation`: NUMERIC(15, 2)
  - `valuation_date`: DATE
  - `is_active`: BOOLEAN — Default `true`
  - `created_at`: TIMESTAMPTZ

#### `RentalUnit`
- **Table**: `coop.rental_units`
- **Fields**:
  - `id`: UUID (PK)
  - `property_id`: UUID (FK → `coop.properties.id`)
  - `unit_number`: VARCHAR(20) — Suite/office/apartment number
  - `monthly_rent`: NUMERIC(15, 2)
  - `is_occupied`: BOOLEAN — Default `false`
  - `tenant_name`: VARCHAR(100) (nullable)
  - `tenant_phone`: VARCHAR(20) (nullable)
  - `lease_start`: DATE (nullable)
  - `lease_end`: DATE (nullable)
  - `created_at`: TIMESTAMPTZ

#### `RentalIncome`
- **Table**: `coop.rental_income`
- **Fields**:
  - `id`: UUID (PK)
  - `rental_unit_id`: UUID (FK → `coop.rental_units.id`)
  - `payment_date`: DATE
  - `amount`: NUMERIC(15, 2) — CHECK `amount > 0`
  - `payment_method`: VARCHAR(50) — Bank transfer, cheque, direct deposit
  - `reference_number`: VARCHAR(100) — Bank reference
  - `period_label`: VARCHAR(20) — e.g., "2026-10"
  - `notes`: TEXT (nullable)
  - `created_at`: TIMESTAMPTZ
  - `created_by`: UUID (FK → `coop.users.id`)

#### `Expense`
- **Table**: `coop.expenses`
- **Fields**:
  - `id`: UUID (PK)
  - `fund_id`: UUID (FK → `coop.funds.id`) — Fund bearing the cost
  - `project_id`: UUID (FK → `coop.projects.id`, nullable) — Optional project link
  - `category`: `ExpenseCategory`
  - `amount`: NUMERIC(15, 2) — CHECK `amount > 0`
  - `expense_date`: DATE
  - `payee`: VARCHAR(100) — Recipient vendor/individual
  - `receipt_reference`: VARCHAR(100) — Receipt / invoice number
  - `description`: TEXT
  - `created_at`: TIMESTAMPTZ
  - `created_by`: UUID (FK → `coop.users.id`)
