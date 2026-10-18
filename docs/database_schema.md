# Cooperative Financial Management ERP — Database Schema Specification

> **Document Status**: Authoritative DDL Specification  
> **Target Engine**: PostgreSQL 16+  
> **Schema**: `coop`  
> **Milestone**: Chapter 02 — Repair the Foundations  

---

## 1. Schema Initialization

```sql
CREATE SCHEMA IF NOT EXISTS coop;
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- For gen_random_uuid()
```

---

## 2. Table Definitions

### 2.1 Identity & Access

#### `coop.users`
```sql
CREATE TABLE coop.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT ck_users_role CHECK (role IN ('ADMIN', 'TREASURER', 'VIEWER'))
);

CREATE INDEX ix_users_role ON coop.users (role);
```

#### `coop.audit_log`
```sql
CREATE TABLE coop.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES coop.users (id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_audit_log_action CHECK (action IN (
        'CREATE', 'UPDATE', 'VERIFY', 'REVERSE', 'APPROVE',
        'REJECT', 'EXIT', 'DEACTIVATE', 'LOGIN', 'CONFIG_CHANGE'
    ))
);

CREATE INDEX ix_audit_log_user_id ON coop.audit_log (user_id);
CREATE INDEX ix_audit_log_entity ON coop.audit_log (entity_type, entity_id);
CREATE INDEX ix_audit_log_created_at ON coop.audit_log (created_at DESC);
```

#### `coop.system_config`
```sql
CREATE TABLE coop.system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(50) NOT NULL,
    config_value TEXT NOT NULL,
    value_type VARCHAR(20) NOT NULL,
    description VARCHAR(255) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES coop.users (id),
    CONSTRAINT uq_system_config_key_effective UNIQUE (config_key, effective_from),
    CONSTRAINT ck_system_config_value_type CHECK (value_type IN ('DECIMAL', 'INTEGER', 'STRING', 'BOOLEAN')),
    CONSTRAINT ck_system_config_dates CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE INDEX ix_system_config_lookup ON coop.system_config (config_key, effective_from, effective_to);
```

---

### 2.2 Member & Equity Domain

#### `coop.members`
```sql
CREATE TABLE coop.members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_number VARCHAR(20) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    address TEXT,
    date_joined DATE NOT NULL,
    date_exited DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    exit_reason TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ,
    created_by UUID NOT NULL REFERENCES coop.users (id),
    CONSTRAINT uq_members_member_number UNIQUE (member_number),
    CONSTRAINT ck_members_status CHECK (status IN ('ACTIVE', 'EXITED', 'SUSPENDED')),
    CONSTRAINT ck_members_exit_dates CHECK (date_exited IS NULL OR date_exited >= date_joined)
);

CREATE INDEX ix_members_status ON coop.members (status);
CREATE INDEX ix_members_phone ON coop.members (phone);
```
> **Classification Note (UBR-17)**: Members can leave the cooperative, receive refundable money under applicable rules, have shares extinguished, and retain permanent historical records (**Confirmed Business Requirement**). The software state machine treats `ACTIVE` → `EXITED` as a one-way technical safeguard to preserve audit trails. Whether an exited member could later be readmitted if membership reopens is an **Unresolved Business Decision**.

#### `coop.shares`
```sql
CREATE TABLE coop.shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES coop.members (id),
    share_count INTEGER NOT NULL,
    value_per_share NUMERIC(15, 2) NOT NULL,
    total_value NUMERIC(15, 2) NOT NULL,
    effective_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES coop.users (id),
    CONSTRAINT ck_shares_count CHECK (share_count >= 0),
    CONSTRAINT ck_shares_value_per_share CHECK (value_per_share > 0),
    CONSTRAINT ck_shares_total_value CHECK (total_value = (share_count * value_per_share))
);

CREATE INDEX ix_shares_member_id ON coop.shares (member_id);
CREATE INDEX ix_shares_effective_date ON coop.shares (effective_date DESC);
```
> **Classification Note (UBR-14)**: 12 shares @ ETB 5,000 = ETB 60,000 is a **Confirmed Business Requirement**. Storing share ownership in a dedicated table separate from `coop.contributions` without automated balance merging is a **Proposed Technical Safeguard** while the accounting relationship between share capital and recurring contributions remains an **Unresolved Business Decision**.

---

### 2.3 Financial Ledger & Funds Domain

#### `coop.funds`
```sql
CREATE TABLE coop.funds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    fund_type VARCHAR(30) NOT NULL,
    description VARCHAR(255) NOT NULL,
    current_balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_funds_name UNIQUE (name),
    CONSTRAINT ck_funds_type CHECK (fund_type IN (
        'MEMBER_EQUITY', 'OPERATING', 'PROJECT', 'RENTAL_INCOME', 'RESERVE'
    ))
);

CREATE INDEX ix_funds_type ON coop.funds (fund_type);
```
> **Classification Note (UBR-18)**: Cooperative income supports normal union operating expenses, and remaining rental-project income is intended for the mall project (**Confirmed Business Requirement**). The `RESERVE` fund type is a **Proposed Technical Safeguard** schema placeholder; whether a formal statutory reserve is mandated by bylaws and the exact allocation formula between funds are **Unresolved Business Decisions**.

#### `coop.transactions` (Append-Only Core Ledger)
```sql
CREATE TABLE coop.transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fund_id UUID NOT NULL REFERENCES coop.funds (id),
    transaction_type VARCHAR(50) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    balance_after NUMERIC(15, 2) NOT NULL,
    member_id UUID REFERENCES coop.members (id),
    reference_type VARCHAR(50) NOT NULL,
    reference_id UUID NOT NULL,
    reversal_of UUID REFERENCES coop.transactions (id),
    description VARCHAR(255) NOT NULL,
    transaction_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES coop.users (id),
    CONSTRAINT ck_transactions_amount CHECK (amount > 0),
    CONSTRAINT ck_transactions_direction CHECK (direction IN ('CREDIT', 'DEBIT')),
    CONSTRAINT ck_transactions_type CHECK (transaction_type IN (
        'MEMBER_CONTRIBUTION', 'OPERATING_CONTRIBUTION', 'WITHDRAWAL', 'EXIT_PAYOUT',
        'RENTAL_INCOME', 'EXPENSE', 'FUND_TRANSFER_IN', 'FUND_TRANSFER_OUT',
        'CORRECTION', 'REVERSAL', 'OPENING_BALANCE'
    ))
);

CREATE INDEX ix_transactions_fund_id ON coop.transactions (fund_id);
CREATE INDEX ix_transactions_member_id ON coop.transactions (member_id);
CREATE INDEX ix_transactions_date ON coop.transactions (transaction_date DESC);
CREATE INDEX ix_transactions_fund_date ON coop.transactions (fund_id, transaction_date DESC);
CREATE INDEX ix_transactions_reference ON coop.transactions (reference_type, reference_id);
CREATE INDEX ix_transactions_reversal_of ON coop.transactions (reversal_of);
```

#### `coop.fund_transfers`
```sql
CREATE TABLE coop.fund_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_fund_id UUID NOT NULL REFERENCES coop.funds (id),
    destination_fund_id UUID NOT NULL REFERENCES coop.funds (id),
    amount NUMERIC(15, 2) NOT NULL,
    description VARCHAR(255) NOT NULL,
    transfer_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES coop.users (id),
    CONSTRAINT ck_fund_transfers_amount CHECK (amount > 0),
    CONSTRAINT ck_fund_transfers_distinct CHECK (source_fund_id <> destination_fund_id)
);

CREATE INDEX ix_fund_transfers_source ON coop.fund_transfers (source_fund_id);
CREATE INDEX ix_fund_transfers_destination ON coop.fund_transfers (destination_fund_id);
```

#### `coop.contributions`
```sql
CREATE TABLE coop.contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES coop.members (id),
    contribution_date DATE NOT NULL,
    member_amount NUMERIC(15, 2) NOT NULL,
    operating_amount NUMERIC(15, 2) NOT NULL,
    total_amount NUMERIC(15, 2) NOT NULL,
    bank_reference VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'RECORDED',
    verified_by UUID REFERENCES coop.users (id),
    verified_at TIMESTAMPTZ,
    period_label VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES coop.users (id),
    CONSTRAINT ck_contributions_member_amount CHECK (member_amount >= 0),
    CONSTRAINT ck_contributions_operating_amount CHECK (operating_amount >= 0),
    CONSTRAINT ck_contributions_total CHECK (total_amount = (member_amount + operating_amount)),
    CONSTRAINT ck_contributions_status CHECK (status IN ('RECORDED', 'VERIFIED', 'DISPUTED'))
);

CREATE INDEX ix_contributions_member_id ON coop.contributions (member_id);
CREATE INDEX ix_contributions_date ON coop.contributions (contribution_date DESC);
CREATE INDEX ix_contributions_status ON coop.contributions (status);
CREATE INDEX ix_contributions_bank_ref ON coop.contributions (bank_reference);
```

#### `coop.withdrawals`
```sql
CREATE TABLE coop.withdrawals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES coop.members (id),
    withdrawal_type VARCHAR(30) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    requested_date DATE NOT NULL,
    approved_by UUID REFERENCES coop.users (id),
    approved_at TIMESTAMPTZ,
    paid_date DATE,
    bank_reference VARCHAR(100),
    reason TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES coop.users (id),
    CONSTRAINT ck_withdrawals_amount CHECK (amount > 0),
    CONSTRAINT ck_withdrawals_type CHECK (withdrawal_type IN ('EXIT_PAYOUT', 'PARTIAL_WITHDRAWAL')),
    CONSTRAINT ck_withdrawals_status CHECK (status IN ('PENDING', 'APPROVED', 'PAID', 'REJECTED'))
);

CREATE INDEX ix_withdrawals_member_id ON coop.withdrawals (member_id);
CREATE INDEX ix_withdrawals_status ON coop.withdrawals (status);
```

#### `coop.bank_accounts`
```sql
CREATE TABLE coop.bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(50) NOT NULL,
    account_holder VARCHAR(100) NOT NULL,
    branch VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_bank_accounts_number UNIQUE (bank_name, account_number)
);
```

---

### 2.4 Projects, Properties & Operations

#### `coop.projects`
```sql
CREATE TABLE coop.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'PLANNING',
    budget NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    spent NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    start_date DATE NOT NULL,
    target_completion_date DATE,
    completion_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES coop.users (id),
    CONSTRAINT ck_projects_status CHECK (status IN (
        'PLANNING', 'UNDER_CONSTRUCTION', 'OPERATIONAL', 'COMPLETED', 'SUSPENDED'
    )),
    CONSTRAINT ck_projects_budget CHECK (budget >= 0),
    CONSTRAINT ck_projects_spent CHECK (spent >= 0)
);

CREATE INDEX ix_projects_status ON coop.projects (status);
```

#### `coop.properties`
```sql
CREATE TABLE coop.properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES coop.projects (id),
    name VARCHAR(100) NOT NULL,
    property_type VARCHAR(50) NOT NULL,
    address TEXT NOT NULL,
    acquisition_cost NUMERIC(15, 2) NOT NULL,
    acquisition_date DATE NOT NULL,
    current_valuation NUMERIC(15, 2) NOT NULL,
    valuation_date DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_properties_cost CHECK (acquisition_cost >= 0),
    CONSTRAINT ck_properties_valuation CHECK (current_valuation >= 0)
);

CREATE INDEX ix_properties_project_id ON coop.properties (project_id);
```

#### `coop.rental_units`
```sql
CREATE TABLE coop.rental_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES coop.properties (id),
    unit_number VARCHAR(20) NOT NULL,
    monthly_rent NUMERIC(15, 2) NOT NULL,
    is_occupied BOOLEAN NOT NULL DEFAULT false,
    tenant_name VARCHAR(100),
    tenant_phone VARCHAR(20),
    lease_start DATE,
    lease_end DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_rental_units_property_unit UNIQUE (property_id, unit_number),
    CONSTRAINT ck_rental_units_rent CHECK (monthly_rent >= 0)
);

CREATE INDEX ix_rental_units_property_id ON coop.rental_units (property_id);
```

#### `coop.rental_income`
```sql
CREATE TABLE coop.rental_income (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rental_unit_id UUID NOT NULL REFERENCES coop.rental_units (id),
    payment_date DATE NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100) NOT NULL,
    period_label VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES coop.users (id),
    CONSTRAINT ck_rental_income_amount CHECK (amount > 0)
);

CREATE INDEX ix_rental_income_unit_id ON coop.rental_income (rental_unit_id);
CREATE INDEX ix_rental_income_date ON coop.rental_income (payment_date DESC);
```

#### `coop.expenses`
```sql
CREATE TABLE coop.expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fund_id UUID NOT NULL REFERENCES coop.funds (id),
    project_id UUID REFERENCES coop.projects (id),
    category VARCHAR(30) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    expense_date DATE NOT NULL,
    payee VARCHAR(100) NOT NULL,
    receipt_reference VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES coop.users (id),
    CONSTRAINT ck_expenses_amount CHECK (amount > 0),
    CONSTRAINT ck_expenses_category CHECK (category IN (
        'ADMINISTRATIVE', 'MAINTENANCE', 'UTILITIES', 'SALARY',
        'TAX', 'LEGAL', 'CONSTRUCTION', 'OTHER'
    ))
);

CREATE INDEX ix_expenses_fund_id ON coop.expenses (fund_id);
CREATE INDEX ix_expenses_project_id ON coop.expenses (project_id);
CREATE INDEX ix_expenses_date ON coop.expenses (expense_date DESC);
```

---

## 3. Immutability Safety Triggers

To guarantee that the core ledger and audit trail cannot be modified or purged through direct SQL commands:

```sql
CREATE OR REPLACE FUNCTION coop.prevent_ledger_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability violation: records in %.% cannot be updated or deleted.',
        TG_TABLE_SCHEMA, TG_TABLE_NAME
        USING ERRCODE = 'restrict_violation';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_immutable_transactions
    BEFORE UPDATE OR DELETE ON coop.transactions
    FOR EACH ROW EXECUTE FUNCTION coop.prevent_ledger_mutation();

CREATE TRIGGER trg_immutable_audit_log
    BEFORE UPDATE OR DELETE ON coop.audit_log
    FOR EACH ROW EXECUTE FUNCTION coop.prevent_ledger_mutation();
```
