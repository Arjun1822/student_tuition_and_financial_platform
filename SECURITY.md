# Security Audit & Hardening Specifications

This document outlines the security architecture, threat model mitigations, encryption standards, and role-based access control policies implemented across the application.

---

## 1. Authentication & Session Security

- **JWT Tokens**:
  - Signed with HMAC-SHA256 (`HS256`) using a cryptographically secure 32+ character key.
  - Standard claim validation: `sub` (User ID), `role` (UserRole enum), `exp` (Expiration timestamp).
  - Short-lived token lifetime (configurable between 30 and 60 minutes).
- **Password Storage**:
  - Bcrypt hashing algorithm managed via Passlib with automatic salt generation and work factor tuning.
  - Plaintext passwords are never logged, serialized, or stored.
- **Client Token Handling**:
  - Stored in browser `localStorage`.
  - Axios client interceptors automatically inject `Authorization: Bearer <TOKEN>` on API requests.
  - Immediate token invalidation and redirect on `401 Unauthorized` responses.

---

## 2. Role-Based Access Control (RBAC)

The system defines 5 hierarchical user roles (`backend/app/core/permissions.py`):

1. **`PLATFORM_ADMIN`**:
   - Universal administrative access across all endpoints, configuration, reconciliation, and audit logs.
2. **`ACADEMIC_ADMIN`**:
   - Manages students, programs, fee schedules, and enrollment workflows.
3. **`SUPPORT_STAFF`**:
   - Records student payments, initiates refund claims, and reviews student balance statements.
4. **`INSTRUCTOR`**:
   - Read-only access to academic curriculum and student rosters.
5. **`LEARNER`**:
   - Restricted to self-service views of their own invoices, payments, and balance statements.

### Enforcement Mechanism
- Endpoints use FastAPI dependency factories `require_role(...)` and `require_permissions([...])`.
- Non-conforming authorization attempts return `403 Forbidden` with operational audit tracking.

---

## 3. Data Protection & Input Sanitization

- **SQL Injection Prevention**:
  - 100% of database queries utilize SQLAlchemy 2.0 ORM with parameterized SQL compilation.
  - Raw string concatenation is strictly banned across all repositories.
- **Input Validation**:
  - Pydantic v2 schemas rigorously enforce data types, string length bounds, positive monetary constraints, regex patterns, and valid enum states.
  - Rejection of unexpected JSON properties via strict validation settings.
- **Monetary Precision & Rounding Attacks**:
  - All financial columns stored as fixed-precision `DECIMAL(12,2)`.
  - Python arithmetic conducted using `decimal.Decimal` with banker's rounding (`ROUND_HALF_UP`) to prevent floating-point calculation drift.
- **Cross-Origin Resource Sharing (CORS)**:
  - Whitelist-only origin enforcement configured in FastAPI middleware.
  - Origins defined via environment variables (`CORS_ORIGINS`).

---

## 4. Audit Trail & Log Protection

- **Immutable Financial Ledger**:
  - All balance-affecting transactions (`INVOICE_GENERATED`, `PAYMENT_ALLOCATED`, `PAYMENT_REVERSED`, `REFUND_PROCESSED`, `LATE_FEE_ASSESSED`) write an un-deletable record to `financial_events`.
  - Captured metadata includes timestamps, actor IDs, prior state, new state, and full monetary delta.
- **Credential Protection in Logs**:
  - Database connection strings, passwords, JWT secrets, and bearer tokens are strictly redacted from application logging outputs.
