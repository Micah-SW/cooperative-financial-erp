# Cooperative Financial Management ERP — Setup & Operations Guide

This guide covers environment configuration, local development setup, database migrations, administrative bootstrapping, testing, and operational procedures for the Cooperative Financial Management ERP backend.

---

## 1. Prerequisites

- **Python**: 3.11+ (Python 3.13 supported)
- **Database**: PostgreSQL 16+ (or SQLite test harness for isolated local testing)
- **Virtual Environment Tool**: `venv` or `virtualenv`
- **Docker & Docker Compose**: Optional for containerized PostgreSQL

---

## 2. Environment Configuration

The application uses `pydantic-settings` to load configurations from environment variables or a `.env` file in `backend/`.

1. Copy `.env.example` to `backend/.env` (or project root `.env`):
   ```bash
   cp .env.example backend/.env
   ```
2. Verify / adjust key variables:
   ```ini
   # Environment mode: development, staging, production
   ENVIRONMENT=development

   # Database connection (PostgreSQL asyncpg)
   DATABASE_URL=postgresql+asyncpg://coop_user:coop_secret@localhost:5432/coop_db

   # JWT & Security
   SECRET_KEY=dev-secret-key-change-in-production-min-32-bytes-long!
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=480

   # Database schema
   DB_SCHEMA=coop

   # Server host & port
   HOST=0.0.0.0
   PORT=8000
   ```

---

## 3. Dependency Installation & Virtual Environment

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   - **Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
3. Install the application and development dependencies in editable mode:
   ```bash
   pip install -e ".[dev]"
   ```

---

## 4. Database Setup & Migrations

The database models target the isolated PostgreSQL schema `coop`.

### A. Development PostgreSQL via Docker Compose
If Docker is installed:
```bash
docker compose up -d postgres
```

### B. Applying Database Migrations (Online)
When PostgreSQL is reachable:
```bash
cd backend
alembic upgrade head
```

### C. Generating Offline Migration SQL (Without Live PostgreSQL)
To inspect or generate the exact DDL statements offline:
```bash
cd backend
alembic upgrade head --sql
```
To generate downgrade SQL:
```bash
alembic downgrade 20261020_0001:base --sql
```

The foundational migration (`20261020_0001_initial_foundations.py`) creates:
1. `coop` schema (if not existing).
2. `coop.users` table, indexes, and unique constraints.
3. `coop.audit_logs` table, indexes, and immutability trigger `trg_audit_logs_immutable`.
4. `coop.system_config` table, date sanity check constraints, and composite unique indexes for effective-dating.

---

## 5. Administrative Bootstrap Mechanism

To prevent exposing passwords in shell command histories or public endpoints, an administrative bootstrap CLI tool is provided.

### Characteristics:
- **Duplicate Prevention**: Rejects bootstrap if an account with `role = ADMIN` already exists.
- **Uniqueness Enforcement**: Rejects collision with existing usernames or emails.
- **Password Strength**: Requires at least 8 characters.
- **Auditing**: Writes an immutable audit log entry for the creation event.
- **Secret Redaction**: Never logs or prints plaintext passwords or hashes.

### Interactive Execution:
```bash
cd backend
python -m app.cli bootstrap-admin --username admin --email admin@coop.local --full-name "System Administrator"
```
You will be prompted securely for a password:
```text
Enter password for initial administrator (min 8 chars): ********
```

### Non-Interactive / Automation Execution:
Set the password in the environment variable:
```bash
export BOOTSTRAP_ADMIN_PASSWORD="SecureBootstrapPassword123!"
python -m app.cli bootstrap-admin --username admin --email admin@coop.local --full-name "System Administrator"
```

---

## 6. Running the Application

Start the FastAPI application with Uvicorn:
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The application entry point exposes:
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Liveness Probe**: `http://localhost:8000/health`
- **Readiness Probe**: `http://localhost:8000/ready` (validates database connectivity)
- **API v1 Routes**: `http://localhost:8000/api/v1`

---

## 7. Running the Automated Test Suite

The test suite contains 64 automated tests (29 foundation tests + 35 Chapter 03 integration/unit tests) running against an isolated SQLite in-memory engine with attached `coop` schema.

Run all tests:
```bash
cd backend
pytest -v
```

Run specific test modules:
```bash
# Application lifespans, health, error envelopes
pytest tests/test_application.py -v

# Authentication, tokens, password hashing, RBAC, bootstrap CLI
pytest tests/test_auth/ -v

# User administration CRUD & deactivation
pytest tests/test_user_admin.py -v

# System configuration & effective-dating
pytest tests/test_config.py -v

# Audit log immutability & redaction
pytest tests/test_audit.py -v

# Alembic migration script validation
pytest tests/test_migration.py -v

# Chapter 02 Foundation tests
pytest tests/test_foundations.py -v
```

---

## 8. Known Operational Limitations & Boundaries

1. **Chapter 03 Scope**:
   - Only foundational models (`User`, `AuditLog`, `SystemConfig`) are active.
   - Business models (`Member`, `Share`, `Contribution`, `Withdrawal`, `Fund`, `Property`, `Project`) are intentionally deferred to subsequent chapters.
2. **Financial Ledger Invariants**:
   - Unresolved business decisions UBR-1 through UBR-18 (see `docs/OPEN_QUESTIONS.md`) are preserved and not prematurely implemented.
3. **Audit Log Database Trigger**:
   - The immutability trigger (`trg_audit_logs_immutable`) is created by PostgreSQL DDL during Alembic migration. When executing in SQLite test environments, application-level restrictions and read-only query surfaces enforce immutability.
