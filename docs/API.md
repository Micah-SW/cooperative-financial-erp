# Cooperative Financial Management ERP — API Reference (v1)

This reference documents the foundational REST API endpoints implemented in **Chapter 03: Wake the Engine**.

Interactive documentation is also served directly by the backend:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema (JSON)**: `http://localhost:8000/openapi.json`

For future business specifications (Members, Shares, Contributions, Funds, Properties, Projects), consult [api_contract.md](file:///c:/Users/Cyberpunk/Documents/mom_company_erp/docs/api_contract.md).

---

## 1. Global Conventions

### Standard Envelope & Formats
- All request and response bodies use JSON (`Content-Type: application/json`).
- Date format: `YYYY-MM-DD` (ISO 8601).
- Timestamp format: `YYYY-MM-DDTHH:MM:SSZ` (ISO 8601 UTC).
- Identifiers: RFC 4122 UUID v4 strings.

### Error Envelope
All error responses adhere to the standard envelope:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of error",
    "details": {}
  }
}
```

Standard HTTP status codes and error codes:
| HTTP Status | Error Code | Description |
| :--- | :--- | :--- |
| `400` | `VALIDATION_ERROR` | Business logic validation failure |
| `401` | `UNAUTHORIZED` | Missing, expired, or invalid bearer token |
| `403` | `FORBIDDEN` | Insufficient permissions for user's role |
| `404` | `NOT_FOUND` | Requested entity does not exist |
| `409` | `DUPLICATE_RESOURCE` | Unique constraint violation (e.g. username/email exists) |
| `422` | `VALIDATION_ERROR` | Request payload schema validation failure |
| `500` | `INTERNAL_ERROR` | Unexpected server error |

---

## 2. Authentication & Authorization

All authenticated endpoints require an HTTP `Authorization` header with a Bearer JWT:
```http
Authorization: Bearer <access_token>
```

### Roles (RBAC)
- `ADMIN`: Full administrative control over users, configuration, and audit logs.
- `TREASURER`: Read access to users and audit logs; view access to configuration; (future financial operations).
- `VIEWER`: Read-only access to specific cooperative reports and configuration.

---

## 3. System & Health Endpoints

### `GET /health`
Liveness probe checking if application process is running.
- **Auth**: None
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "app": "Cooperative Financial Management ERP",
  "version": "0.1.0",
  "timestamp": "2026-10-20T11:00:00Z"
}
```

### `GET /ready` (or `/readiness`)
Readiness probe checking backend dependencies (PostgreSQL database connectivity).
- **Auth**: None
- **Response**: `200 OK` (when DB connected) or `503 Service Unavailable`
```json
{
  "status": "ready",
  "database": "connected",
  "timestamp": "2026-10-20T11:00:00Z"
}
```

---

## 4. Authentication Endpoints (`/api/v1/auth`)

### `POST /api/v1/auth/login`
Authenticate user with username/password and issue JWT access token.
- **Auth**: None
- **Request Body**:
  ```json
  {
    "username": "admin",
    "password": "SecurePassword123!"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "user": {
      "id": "73c683ee-82c5-4a6f-998e-4a6c4b281f7c",
      "username": "admin",
      "email": "admin@coop.local",
      "full_name": "System Administrator",
      "role": "ADMIN",
      "is_active": true
    }
  }
  ```
- **Errors**: `401 Unauthorized` for invalid credentials or deactivated accounts.

### `GET /api/v1/auth/me`
Retrieve profile of currently authenticated user.
- **Auth**: Bearer token
- **Response**: `200 OK` (`UserResponse` schema)

### `POST /api/v1/auth/change-password`
Change password for the currently authenticated user.
- **Auth**: Bearer token
- **Request Body**:
  ```json
  {
    "current_password": "OldPassword123!",
    "new_password": "NewSecurePassword456!"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "message": "Password changed successfully"
  }
  ```

---

## 5. User Administration Endpoints (`/api/v1/users`)

All endpoints in this section require `ADMIN` role.

### `GET /api/v1/users`
List users with pagination and optional role filtering.
- **Auth**: `ADMIN`
- **Query Parameters**:
  - `role` (optional): `ADMIN` | `TREASURER` | `VIEWER`
  - `page` (optional, default `1`): Page number
  - `per_page` (optional, default `25`, max `100`): Items per page
- **Response**: `200 OK` (`PaginatedResult[UserSummary]`)

### `POST /api/v1/users`
Create a new user account.
- **Auth**: `ADMIN`
- **Request Body**:
  ```json
  {
    "username": "treasurer1",
    "email": "treasurer1@coop.local",
    "full_name": "Coop Treasurer",
    "role": "TREASURER",
    "password": "TemporaryPassword123!"
  }
  ```
- **Response**: `201 Created` (`UserResponse`)
- **Errors**: `409 Conflict` if username or email already exists.

### `GET /api/v1/users/{id}`
Retrieve user details by UUID.
- **Auth**: `ADMIN`
- **Response**: `200 OK` (`UserResponse`)
- **Errors**: `404 Not Found` if user does not exist.

### `PUT /api/v1/users/{id}`
Update user profile, role, or active status.
- **Auth**: `ADMIN`
- **Request Body**:
  ```json
  {
    "email": "new_email@coop.local",
    "full_name": "Updated Name",
    "role": "VIEWER",
    "is_active": true
  }
  ```
- **Response**: `200 OK` (`UserResponse`)

### `DELETE /api/v1/users/{id}`
Deactivate a user account (soft deactivation; physical deletion is prohibited).
- **Auth**: `ADMIN`
- **Response**: `200 OK` (`UserResponse` with `is_active: false`)

---

## 6. System Configuration Endpoints (`/api/v1/config`)

### `GET /api/v1/config`
Retrieve all current active configuration key-values.
- **Auth**: `ADMIN` | `TREASURER` | `VIEWER`
- **Response**: `200 OK` (`list[ConfigValue]`)
  ```json
  [
    {
      "config_key": "SHARE_VALUE",
      "config_value": "100.00",
      "value_type": "DECIMAL",
      "description": "Face value per cooperative share in ETB",
      "effective_from": "2026-01-01",
      "effective_to": null
    }
  ]
  ```

### `GET /api/v1/config/{key}`
Retrieve active configuration value for a specific key.
- **Auth**: `ADMIN` | `TREASURER` | `VIEWER`
- **Query Parameters**:
  - `as_of` (optional, `YYYY-MM-DD`): Historical point-in-time lookup
- **Response**: `200 OK` (`ConfigValue`)

### `PUT /api/v1/config/{key}`
Update configuration value using effective-dating rules.
- **Auth**: `ADMIN` only
- **Behavior**:
  - Validates value against declared `value_type`.
  - Closes preceding active record (`effective_to = new_effective_from - 1 day`).
  - Inserts new active record (`effective_from = new_effective_from`, `effective_to = NULL`).
  - Records an `UPDATE` audit log.
- **Request Body**:
  ```json
  {
    "config_value": "150.00",
    "effective_from": "2026-11-01",
    "description": "Updated share face value"
  }
  ```
- **Response**: `200 OK` (`ConfigValue`)

### `GET /api/v1/config/{key}/history`
Retrieve full chronological audit history for a configuration key.
- **Auth**: `ADMIN` only
- **Response**: `200 OK` (`ConfigHistory`)

---

## 7. Audit Log Endpoints (`/api/v1/audit-logs`)

### `GET /api/v1/audit-logs`
Query immutable audit events with pagination and filters.
- **Auth**: `ADMIN` | `TREASURER`
- **Query Parameters**:
  - `user_id` (optional, UUID): Filter by actor
  - `action` (optional): `CREATE` | `UPDATE` | `DELETE` | `LOGIN` | `LOGIN_FAILED` | `PASSWORD_CHANGE` | `EXPORT` | `APPROVE` | `REJECT` | `REVERSE`
  - `entity_type` (optional): Filter by entity class (e.g. `User`, `SystemConfig`)
  - `from_date` (optional, timestamp / date): Start filter
  - `to_date` (optional, timestamp / date): End filter
  - `page` (optional, default `1`): Page number
  - `per_page` (optional, default `25`, max `100`): Items per page
- **Response**: `200 OK` (`PaginatedResult[AuditLogResponse]`)
  ```json
  {
    "items": [
      {
        "id": "e60f082e-9d2a-4ce4-89c5-8ee85fb034b7",
        "created_at": "2026-10-20T11:30:00Z",
        "user_id": "73c683ee-82c5-4a6f-998e-4a6c4b281f7c",
        "action": "UPDATE",
        "entity_type": "SystemConfig",
        "entity_id": "a4d8fae0-1c31-48e0-bb15-373eaef52fbf",
        "old_values": {"config_value": "100.00"},
        "new_values": {"config_value": "150.00"},
        "ip_address": "127.0.0.1"
      }
    ],
    "total": 1,
    "page": 1,
    "per_page": 25,
    "total_pages": 1
  }
  ```
- **Security Guarantee**: Sensitive fields (`password`, `access_token`, `token`, `secret`, `hashed_password`) are permanently sanitized as `[REDACTED]` prior to persistence.

---

## 8. Member Management Endpoints (`/api/v1/members`)

### `GET /api/v1/members`
Retrieve paginated list of cooperative members with summary share balances.
- **Auth**: `ADMIN` | `TREASURER` | `VIEWER`
- **Query Parameters**:
  - `status` (optional): Filter by `MemberStatus` (`ACTIVE` | `EXITED` | `SUSPENDED`)
  - `search` (optional): Case-insensitive substring match across `member_number`, `full_name`, and `phone`
  - `page` (optional, default `1`): Page number
  - `per_page` (optional, default `25`, max `100`): Items per page
- **Response**: `200 OK` (`PaginatedResult[MemberSummary]`)
  ```json
  {
    "items": [
      {
        "id": "7b524670-3982-4fcf-8472-353d9e334df5",
        "member_number": "M-0001",
        "full_name": "Abebe Kebede",
        "phone": "+251911223344",
        "status": "ACTIVE",
        "date_joined": "2024-01-15",
        "current_share_count": 12,
        "current_share_value": "60000.00"
      }
    ],
    "total": 1,
    "page": 1,
    "per_page": 25,
    "total_pages": 1
  }
  ```

### `POST /api/v1/members`
Register a new member and allocate initial shares.
- **Auth**: `ADMIN` only
- **Behavior**:
  - Requires `MEMBERSHIP_OPEN` configuration to be explicitly `true`. Fails closed with `400 VALIDATION_ERROR` if absent or false.
  - Requires unique `member_number`. Returns `409 DUPLICATE_RESOURCE` on collision.
  - Automatically queries `SHARE_VALUE` (e.g. ETB 5,000.00) and `SHARES_PER_MEMBER` (e.g. 12) from `ConfigService`.
  - Atomically creates member, initial share record, and `CREATE` audit log.
- **Request Body**:
  ```json
  {
    "member_number": "M-0001",
    "full_name": "Abebe Kebede",
    "phone": "+251911223344",
    "email": "abebe@example.com",
    "address": "Bole Subcity, Woreda 03",
    "date_joined": "2024-01-15",
    "notes": "Founding member"
  }
  ```
- **Response**: `201 Created` (`MemberDetail`)

### `GET /api/v1/members/{id}`
Retrieve complete member profile and chronological share history.
- **Auth**: `ADMIN` | `TREASURER` | `VIEWER`
- **Response**: `200 OK` (`MemberDetail`)
  ```json
  {
    "id": "7b524670-3982-4fcf-8472-353d9e334df5",
    "member_number": "M-0001",
    "full_name": "Abebe Kebede",
    "phone": "+251911223344",
    "email": "abebe@example.com",
    "address": "Bole Subcity, Woreda 03",
    "status": "ACTIVE",
    "date_joined": "2024-01-15",
    "date_exited": null,
    "exit_reason": null,
    "notes": "Founding member",
    "current_share_count": 12,
    "current_share_value": "60000.00",
    "shares": [
      {
        "id": "a1834271-e945-4299-ba6b-4e6378e9f5b2",
        "member_id": "7b524670-3982-4fcf-8472-353d9e334df5",
        "share_count": 12,
        "value_per_share": "5000.00",
        "total_value": "60000.00",
        "effective_date": "2024-01-15",
        "created_at": "2024-01-15T09:00:00Z"
      }
    ]
  }
  ```

### `PUT /api/v1/members/{id}`
Update mutable contact and profile information for a member.
- **Auth**: `ADMIN` only
- **Immutability Protection**: `member_number` and `status` are strictly immutable. Supplying either field produces an explicit `422 VALIDATION_ERROR`.
- **Request Body**:
  ```json
  {
    "full_name": "Abebe Kebede Worku",
    "phone": "+251911998877",
    "email": "abebe.worku@example.com",
    "address": "Yeka Subcity, Woreda 08",
    "notes": "Updated contact details"
  }
  ```
- **Response**: `200 OK` (`MemberDetail`)

### `POST /api/v1/members/{id}/exit`
Process member exit lifecycle transition.
- **Auth**: `ADMIN` only
- **Behavior**:
  - Enforces one-way `ACTIVE` → `EXITED` transition (rejects if already `EXITED` or not `ACTIVE`).
  - Appends an extinguishing share-history record (`share_count = 0`, `total_value = 0.00`), preserving all historical records.
  - Emits `EXIT` audit log.
  - **Strict Scope Boundary**: Performs membership lifecycle transition and share extinguishing only. Does NOT compute exit settlements, issue payouts, or generate financial ledger transactions (deferred to Chapter 05 per UBR-1 / UBR-3).
- **Request Body**:
  ```json
  {
    "exit_date": "2026-10-22",
    "exit_reason": "Relocating abroad",
    "notes": "Membership terminated"
  }
  ```
- **Response**: `200 OK` (`MemberDetail`)
