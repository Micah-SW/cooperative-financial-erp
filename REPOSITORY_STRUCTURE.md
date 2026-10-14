# REPOSITORY_STRUCTURE.md — Cooperative Financial Management ERP

> **Document Status**: Structural Reference — Source of Truth  
> **Last Updated**: 2026-09-05  
> **Total Files**: 135 | **Config/Implemented**: 12 | **Skeleton**: 123

---

## Complete Directory Tree

```
mom_company_erp/
│
├── .gitignore                              # Git ignore rules
├── ARCHITECTURE.md                         # System architecture blueprint (16 sections)
├── MODULE_MAP.md                           # Module definitions and dependencies
├── REPOSITORY_STRUCTURE.md                 # THIS FILE — structural reference
├── docker-compose.yml                      # Development Docker Compose (PostgreSQL + backend)
│
├── backend/                                # Python / FastAPI backend
│   ├── .env.example                        # Environment variable template
│   ├── Dockerfile                          # Backend container definition
│   ├── pyproject.toml                      # Python project config + dependencies
│   ├── alembic.ini                         # Alembic migration configuration
│   │
│   ├── alembic/                            # Database migrations
│   │   ├── env.py                          # Migration environment (async)
│   │   ├── script.py.mako                  # Migration script template
│   │   └── versions/                       # Auto-generated migration files
│   │       └── .gitkeep
│   │
│   ├── app/                                # Application source code
│   │   ├── __init__.py
│   │   ├── main.py                         # FastAPI app creation + middleware + exception handlers
│   │   ├── config.py                       # Pydantic Settings (env vars)
│   │   ├── database.py                     # SQLAlchemy async engine + session factory
│   │   │
│   │   ├── core/                           # ── CROSS-CUTTING CONCERNS ──
│   │   │   ├── __init__.py
│   │   │   ├── enums.py                    # ✅ IMPLEMENTED — All 12 enumerations
│   │   │   ├── exceptions.py               # ✅ IMPLEMENTED — 7-class exception hierarchy
│   │   │   ├── security.py                 # JWT + bcrypt password hashing
│   │   │   ├── dependencies.py             # FastAPI Depends: get_db, get_current_user, require_role
│   │   │   ├── audit.py                    # AuditService — append-only event logging
│   │   │   └── pagination.py               # PaginatedResult<T> + paginate() helper
│   │   │
│   │   ├── models/                         # ── SQLALCHEMY ORM MODELS ──
│   │   │   ├── __init__.py                 # Central import registry (for Alembic)
│   │   │   ├── base.py                     # CoopBase — abstract base with UUID PK + timestamps
│   │   │   ├── user.py                     # User (identity + access)
│   │   │   ├── audit_log.py                # AuditLog (append-only events)
│   │   │   ├── system_config.py            # SystemConfig (effective-dated key-value)
│   │   │   ├── member.py                   # Member (cooperative member)
│   │   │   ├── share.py                    # Share (member equity ownership)
│   │   │   ├── contribution.py             # Contribution (member deposits)
│   │   │   ├── withdrawal.py               # Withdrawal (member payouts)
│   │   │   ├── transaction.py              # Transaction (IMMUTABLE financial ledger)
│   │   │   ├── fund.py                     # Fund + FundTransfer (fund accounts)
│   │   │   ├── bank_account.py             # BankAccount (reference entity)
│   │   │   ├── project.py                  # Project (investment projects)
│   │   │   ├── property.py                 # Property (physical assets)
│   │   │   ├── rental.py                   # RentalUnit + RentalIncome
│   │   │   └── expense.py                  # Expense (cooperative expenses)
│   │   │
│   │   ├── schemas/                        # ── PYDANTIC REQUEST/RESPONSE SCHEMAS ──
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                     # LoginRequest, LoginResponse, TokenPayload
│   │   │   ├── user.py                     # UserCreate, UserUpdate, UserResponse
│   │   │   ├── config.py                   # ConfigValue, ConfigUpdate, ConfigHistory
│   │   │   ├── member.py                   # MemberCreate/Update/Exit/Summary/Detail
│   │   │   ├── contribution.py             # ContributionCreate/Verify/Reverse/Response
│   │   │   ├── withdrawal.py               # WithdrawalCreate/MarkPaid/Response
│   │   │   ├── fund.py                     # FundResponse, FundTransferCreate, ReconciliationResult
│   │   │   ├── transaction.py              # TransactionResponse (read-only)
│   │   │   ├── project.py                  # ProjectCreate/Update/Response
│   │   │   ├── property.py                 # Property/RentalUnit/RentalIncome schemas
│   │   │   ├── expense.py                  # ExpenseCreate/Response
│   │   │   └── report.py                   # All report response types + DashboardMetrics
│   │   │
│   │   ├── services/                       # ── BUSINESS LOGIC LAYER ──
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py             # Authentication: login, password change
│   │   │   ├── config_service.py           # Config CRUD with effective dating
│   │   │   ├── member_service.py           # Member lifecycle: create → exit
│   │   │   ├── contribution_service.py     # Record, verify, reverse contributions
│   │   │   ├── withdrawal_service.py       # Create, approve, reject, pay withdrawals
│   │   │   ├── transaction_service.py      # INTERNAL: immutable ledger operations
│   │   │   ├── fund_service.py             # Fund management, transfers, reconciliation
│   │   │   ├── project_service.py          # Project CRUD
│   │   │   ├── property_service.py         # Property/unit CRUD + rental income
│   │   │   ├── expense_service.py          # Expense recording
│   │   │   └── report_service.py           # Read-only reporting + dashboard
│   │   │
│   │   ├── api/                            # ── FASTAPI ROUTERS ──
│   │   │   ├── __init__.py
│   │   │   ├── router.py                   # Top-level router aggregation (/api/v1)
│   │   │   └── v1/                         # Version 1 endpoints
│   │   │       ├── __init__.py
│   │   │       ├── auth.py                 # POST /login, GET /me, POST /change-password
│   │   │       ├── members.py              # CRUD + exit
│   │   │       ├── contributions.py        # Record, verify, reverse
│   │   │       ├── withdrawals.py          # Create, approve, reject, mark-paid
│   │   │       ├── funds.py                # List, detail, transactions, transfer
│   │   │       ├── transactions.py         # READ-ONLY listing
│   │   │       ├── projects.py             # CRUD
│   │   │       ├── properties.py           # Properties + units + rental income
│   │   │       ├── expenses.py             # List + record
│   │   │       ├── config.py               # Read + update
│   │   │       └── reports.py              # All report endpoints
│   │   │
│   │   └── utils/                          # ── PURE UTILITIES ──
│   │       ├── __init__.py
│   │       └── money.py                    # ✅ PARTIAL — Decimal rounding for currency
│   │
│   └── tests/                              # ── BACKEND TESTS ──
│       ├── __init__.py
│       ├── conftest.py                     # Fixtures: test DB, client, factories
│       ├── test_auth/                      # Auth tests
│       ├── test_members/                   # Member lifecycle tests
│       ├── test_contributions/             # Contribution workflow tests
│       ├── test_withdrawals/               # Withdrawal workflow tests
│       ├── test_funds/                     # Fund + transfer tests
│       ├── test_transactions/              # Ledger integrity tests
│       ├── test_properties/                # Property + rental tests
│       ├── test_expenses/                  # Expense tests
│       └── test_reports/                   # Report accuracy tests
│
├── frontend/                               # React / TypeScript / Tailwind frontend
│   ├── .env.example                        # Frontend environment template
│   ├── index.html                          # Single-page app HTML host
│   ├── package.json                        # Node dependencies and scripts
│   ├── postcss.config.js                   # PostCSS configuration
│   ├── tailwind.config.js                  # Tailwind styling configuration
│   ├── tsconfig.json                       # TypeScript compiler configuration
│   ├── tsconfig.node.json                  # TypeScript config for Vite
│   ├── vite.config.ts                      # Vite build configuration + API proxy
│   ├── public/                             # Static assets
│   │
│   └── src/
│       ├── main.tsx                        # React bootstrap
│       ├── App.tsx                         # Routing + AuthProvider wrapper
│       ├── index.css                       # Global styles + Tailwind directives
│       │
│       ├── api/                            # ── API CLIENT LAYER ──
│       │   ├── client.ts                   # Axios/fetch wrapper + JWT interceptor
│       │   ├── auth.ts                     # Auth API calls
│       │   ├── members.ts                  # Members API calls
│       │   ├── contributions.ts            # Contributions API calls
│       │   ├── funds.ts                    # Funds API calls
│       │   ├── properties.ts              # Properties + rental API calls
│       │   ├── expenses.ts                 # Expenses API calls
│       │   └── reports.ts                  # Reports API calls
│       │
│       ├── components/                     # ── UI COMPONENTS ──
│       │   ├── ui/                         # Design system primitives
│       │   │   └── index.ts                # DataTable, Modal, Button, Card, Badge, etc.
│       │   ├── layout/                     # App shell
│       │   │   └── index.ts                # Layout, Sidebar, Header
│       │   ├── common/                     # Domain-aware reusable components
│       │   │   └── index.ts                # MemberSelect, FundSelect, MoneyDisplay, etc.
│       │   ├── members/                    # Member-specific components
│       │   ├── contributions/              # Contribution-specific components
│       │   ├── funds/                      # Fund-specific components
│       │   ├── properties/                 # Property-specific components
│       │   └── expenses/                   # Expense-specific components
│       │
│       ├── pages/                          # ── ROUTE-LEVEL PAGES ──
│       │   ├── LoginPage.tsx
│       │   ├── DashboardPage.tsx
│       │   ├── MembersPage.tsx
│       │   ├── MemberDetailPage.tsx
│       │   ├── MemberStatementPage.tsx
│       │   ├── ContributionsPage.tsx
│       │   ├── FundsPage.tsx
│       │   ├── FundDetailPage.tsx
│       │   ├── PropertiesPage.tsx
│       │   ├── PropertyDetailPage.tsx
│       │   ├── ExpensesPage.tsx
│       │   ├── ReportsPage.tsx
│       │   └── SettingsPage.tsx
│       │
│       ├── hooks/                          # ── CUSTOM REACT HOOKS ──
│       │   └── index.ts                    # useMembers, useContributions, useFunds, etc.
│       │
│       ├── context/                        # ── REACT CONTEXT PROVIDERS ──
│       │   └── AuthContext.tsx             # Auth state, login/logout, role checking
│       │
│       ├── types/                          # ── TYPESCRIPT TYPE DEFINITIONS ──
│       │   └── index.ts                    # All interfaces mirroring backend schemas
│       │
│       └── utils/                          # ── FRONTEND UTILITIES ──
│           └── index.ts                    # formatMoney, formatDate, statusColor, etc.
│
├── infrastructure/                         # ── DEPLOYMENT INFRASTRUCTURE ──
│   ├── docker/
│   │   └── docker-compose.prod.yml         # Production Docker Compose (future)
│   └── nginx/
│       └── nginx.conf                      # Reverse proxy config (future)
│
└── docs/                                   # ── DOCUMENTATION ──
    ├── SETUP.md                            # Setup and development guide
    └── API.md                              # API reference (auto-generated from FastAPI)
```

---

## Directory Purposes

### Root Level

| Path | Purpose |
|---|---|
| `ARCHITECTURE.md` | System architecture blueprint — the complete design reference |
| `MODULE_MAP.md` | Module definitions, dependencies, and acceptance criteria |
| `REPOSITORY_STRUCTURE.md` | This document — structural guide for navigation |
| `docker-compose.yml` | Development environment (PostgreSQL + backend) |
| `.gitignore` | Standard exclusions for Python, Node, IDE, OS |

---

### Backend (`backend/`)

| Directory | Purpose | Naming Convention |
|---|---|---|
| `app/` | Application source code | — |
| `app/core/` | Cross-cutting concerns: auth, audit, config, enums, exceptions | Feature-based |
| `app/models/` | SQLAlchemy ORM models — one file per entity | Entity name: `member.py` |
| `app/schemas/` | Pydantic request/response schemas | Entity name: `member.py` |
| `app/services/` | Business logic — one service class per domain area | `{entity}_service.py` |
| `app/api/v1/` | FastAPI route handlers — thin, delegate to services | Entity name: `members.py` |
| `app/utils/` | Pure utility functions (no domain logic) | Feature name: `money.py` |
| `alembic/` | Database migration scripts | Auto-generated by Alembic |
| `tests/` | pytest test suites — one directory per domain | `test_{entity}/` |

### Frontend (`frontend/`)

| Directory | Purpose | Naming Convention |
|---|---|---|
| `src/api/` | HTTP client wrapper + typed API modules | Entity name: `members.ts` |
| `src/components/ui/` | Reusable design system primitives | Component name: `DataTable.tsx` |
| `src/components/layout/` | App shell: sidebar, header, content area | `Layout.tsx`, `Sidebar.tsx` |
| `src/components/common/` | Domain-aware reusable components | `MemberSelect.tsx` |
| `src/components/{domain}/` | Domain-specific component groups | `MemberTable.tsx` |
| `src/pages/` | Route-level page components | `{Name}Page.tsx` |
| `src/hooks/` | Custom React hooks for data fetching | `useMembers.ts` |
| `src/context/` | React context providers | `AuthContext.tsx` |
| `src/types/` | TypeScript interfaces mirroring backend | `index.ts` |
| `src/utils/` | Frontend utility functions | `index.ts` |

### Infrastructure (`infrastructure/`)

| Directory | Purpose |
|---|---|
| `docker/` | Production Docker Compose and related configs |
| `nginx/` | Reverse proxy configuration for production |

### Documentation (`docs/`)

| File | Purpose |
|---|---|
| `SETUP.md` | Development environment setup guide |
| `API.md` | API reference (links to FastAPI auto-docs) |

---

## File Status Legend

| Status | Meaning |
|---|---|
| ✅ IMPLEMENTED | Production-ready code, fully functional |
| 🔨 SKELETON | Structural placeholder with responsibility docs and TODO markers |
| 📋 CONFIG | Configuration file (complete) |

---

## Implementation Status

### Fully Implemented (3 files)
| File | Description |
|---|---|
| `backend/app/core/enums.py` | All 12 canonical enumerations |
| `backend/app/core/exceptions.py` | 7-class domain exception hierarchy |
| `backend/app/utils/money.py` | Decimal rounding helper (partial) |

### Configuration Files (9 files)
| File | Description |
|---|---|
| `backend/pyproject.toml` | Python dependencies and tool config |
| `backend/.env.example` | Environment variable template |
| `backend/Dockerfile` | Backend container definition |
| `backend/alembic.ini` | Alembic migration config |
| `backend/alembic/script.py.mako` | Migration script template |
| `docker-compose.yml` | Dev environment orchestration |
| `.gitignore` | Git exclusion rules |
| `infrastructure/nginx/nginx.conf` | Nginx placeholder |
| `infrastructure/docker/docker-compose.prod.yml` | Production compose placeholder |

### Skeleton Files (101 files)
All remaining files are structural skeletons with:
- Module/class/function names defined
- Responsibility documentation
- TODO markers for Gemini
- Dependency declarations
- "Must NOT" boundary rules

---

## Layer → File Count Summary

| Layer | Files | Status |
|---|---|---|
| Core (security, auth, audit, config) | 6 | 2 implemented, 4 skeleton |
| ORM Models | 14 | All skeleton |
| Pydantic Schemas | 12 | All skeleton |
| Services | 11 | All skeleton |
| API Routers | 12 | All skeleton |
| Tests | 11 | All skeleton |
| Frontend API | 8 | All skeleton |
| Frontend Components | 3 index files + empty dirs | All skeleton |
| Frontend Pages | 13 | All skeleton |
| Frontend State/Hooks | 3 | All skeleton |
| Infrastructure | 2 | Placeholders |
| Documentation | 2 | Placeholders |

---

## Gemini Implementation Order

Follow the phases in [ARCHITECTURE.md](file:///c:/Users/Cyberpunk/Documents/mom_company_erp/ARCHITECTURE.md) → Section 8:

### Phase 1 — Foundation
```
backend/app/config.py
backend/app/database.py
backend/app/models/base.py
backend/app/core/security.py
backend/app/core/dependencies.py
backend/app/core/pagination.py
backend/app/core/audit.py
backend/app/models/user.py
backend/app/models/audit_log.py
backend/app/models/system_config.py
backend/app/schemas/auth.py
backend/app/schemas/user.py
backend/app/schemas/config.py
backend/app/services/auth_service.py
backend/app/services/config_service.py
backend/app/api/v1/auth.py
backend/app/api/v1/config.py
backend/app/api/router.py
backend/app/main.py
backend/alembic/env.py
→ First migration: create schema + users + audit_log + system_config + seed data
→ Tests: test_auth/
```

### Phase 2 — Members
```
backend/app/models/member.py
backend/app/models/share.py
backend/app/schemas/member.py
backend/app/services/member_service.py
backend/app/api/v1/members.py
→ Migration: members + shares tables
→ Tests: test_members/
```

### Phase 3 — Financial Core
```
backend/app/models/fund.py
backend/app/models/transaction.py
backend/app/models/contribution.py
backend/app/models/withdrawal.py
backend/app/models/bank_account.py
backend/app/schemas/fund.py
backend/app/schemas/transaction.py
backend/app/schemas/contribution.py
backend/app/schemas/withdrawal.py
backend/app/services/transaction_service.py
backend/app/services/fund_service.py
backend/app/services/contribution_service.py
backend/app/services/withdrawal_service.py
backend/app/api/v1/funds.py
backend/app/api/v1/transactions.py
backend/app/api/v1/contributions.py
backend/app/api/v1/withdrawals.py
→ Migration: funds + transactions + contributions + withdrawals + bank_accounts + seed funds
→ Tests: test_funds/, test_transactions/, test_contributions/, test_withdrawals/
```

### Phase 4 — Property & Expenses
```
backend/app/models/project.py
backend/app/models/property.py
backend/app/models/rental.py
backend/app/models/expense.py
backend/app/schemas/project.py
backend/app/schemas/property.py
backend/app/schemas/expense.py
backend/app/services/project_service.py
backend/app/services/property_service.py
backend/app/services/expense_service.py
backend/app/api/v1/projects.py
backend/app/api/v1/properties.py
backend/app/api/v1/expenses.py
→ Migration: projects + properties + rental_units + rental_income + expenses
→ Tests: test_properties/, test_expenses/
```

### Phase 5 — Reporting + Frontend
```
backend/app/schemas/report.py
backend/app/services/report_service.py
backend/app/api/v1/reports.py
→ Tests: test_reports/
→ Begin frontend implementation
```

---

## Cross-Reference Documents

| Document | Location | Purpose |
|---|---|---|
| Architecture Blueprint | [`ARCHITECTURE.md`](file:///c:/Users/Cyberpunk/Documents/mom_company_erp/ARCHITECTURE.md) | System design, flows, decisions, risks |
| Module Map | [`MODULE_MAP.md`](file:///c:/Users/Cyberpunk/Documents/mom_company_erp/MODULE_MAP.md) | Module specs, acceptance criteria |
| Domain Model | `domain_model.md` (artifacts) | Entity field specifications |
| Database Schema | `database_schema.md` (artifacts) | DDL, constraints, indexes |
| API Contract | `api_contract.md` (artifacts) | REST endpoint specifications |
| Service Contracts | `service_contracts.md` (artifacts) | Method signatures, invariants |
| Implementation Plan | `implementation_plan.md` (artifacts) | Phases, timeline, verification |
