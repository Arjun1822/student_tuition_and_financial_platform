# Architecture Overview

The Student Financial Management Platform follows a strict 3-tier enterprise architecture designed for data consistency, financial auditability, high availability, and operational traceability.

---

## 1. Architectural Layers

```
+-----------------------------------------------------------------------+
|                             PRESENTATION TIER                         |
|  React 18 + Vite SPA  |  Tailwind CSS  |  Recharts  |  React Router   |
|  - Module Detail & List Views (Students, Programs, Invoices)          |
|  - Financial Operation Views (Payments, Scholarships, Refunds)        |
|  - Auditing & Compliance Views (Ledger, Reconciliation, Anomalies)    |
|  - Executive Analytics Dashboard                                      |
+-----------------------------------+-----------------------------------+
                                    |
                                    | HTTP / REST (JWT Auth)
                                    v
+-----------------------------------+-----------------------------------+
|                              BUSINESS TIER                            |
|             FastAPI Application (Python 3.12 + Pydantic v2)           |
|                                                                       |
|  [ API Layer / Endpoints ]                                            |
|   - Authentication & Role-Based Access Control (RBAC)                 |
|   - Academic Resources & Invoices Router                              |
|   - Financial Lifecycle & Ledger Routers                              |
|                                                                       |
|  [ Business Domain Services ]                                         |
|   - InvoiceGenerationService    - ScholarshipEligibilityService       |
|   - PaymentAllocationService    - RefundManagementService             |
|   - BalanceCalculationService   - ReconciliationAuditEngine           |
|   - AnomalyDetectionService     - ImmutableAuditService               |
|                                                                       |
|  [ Data Access Layer ]                                                |
|   - Repository Pattern (SQLAlchemy 2.0 ORM over 19 Models)            |
+-----------------------------------+-----------------------------------+
                                    |
                                    | SQL / Connection Pool (PyMySQL)
                                    v
+-----------------------------------+-----------------------------------+
|                                DATA TIER                              |
|                            MySQL 8.0 Engine                           |
|  - InnoDB Storage Engine with Foreign Key Referential Integrity       |
|  - Decimal(12,2) Fixed-Precision Monetary Storage                     |
|  - Compound & B-Tree Indexes on Natural Keys & Filtering Fields       |
|  - Append-Only Immutable Event & Audit Logs                           |
+-----------------------------------------------------------------------+
```

---

## 2. Component Design & Patterns

### 2.1 Backend Architecture
1. **API Routing (`app/api/v1/endpoints/`)**:
   - Thin HTTP controllers responsible for request validation, authorization checks, and HTTP response formatting.
   - Mounted modularly with semantic URL prefixes.
2. **Business Services (`app/services/`)**:
   - Encapsulates domain logic independently of transport.
   - Enforces transactional boundaries using database session context managers.
   - Implements exact financial calculations using Python's `Decimal` module with `ROUND_HALF_UP` arithmetic.
3. **Repository Pattern (`app/repositories/`)**:
   - Isolates SQLAlchemy queries from business logic.
   - Standardizes filtering, pagination, and eager loading (`joinedload`) to prevent N+1 query overhead.
4. **Data Models (`app/models/`)**:
   - SQLAlchemy 2.0 declarative models with explicit foreign key constraints (`ondelete="RESTRICT"`), index definitions, and enum types.
5. **Schema Layer (`app/schemas/`)**:
   - Pydantic v2 models for strict request validation, data serialization, and OpenAPI documentation generation.

### 2.2 Frontend Architecture
1. **API Client Layer (`frontend/src/api/`)**:
   - Axios instance with request interceptors for automatic JWT token injection and response interceptors for 401 handling.
2. **Context & State Management (`frontend/src/context/`)**:
   - `AuthContext` provides global authentication status, user profile, and token persistence in local storage.
3. **Reusable Component System (`frontend/src/components/`)**:
   - `Modal`: Accessible dialog wrapper for forms and detail inspection.
   - `StatusBadge`: Unified status pill coloring across all lifecycle states.
   - `Pagination`: Reusable pagination controls.
   - `Sidebar` & `Navbar`: Consistent responsive navigation shell.
4. **Code Splitting & Optimization**:
   - Modular chunk separation configured in Vite Rollup options:
     - `vendor-react`: Core React ecosystem.
     - `vendor-charts`: Recharts visual components.
     - `vendor-icons`: Lucide React icon set.
     - `index`: Application domain pages and routing.

---

## 3. Data Flow Workflows

### 3.1 Enrollment to Invoice Lifecycle
1. Student enrolled in Academic Program for a specific Term.
2. `InvoiceGenerationService` looks up active `FeeSchedule` for (Program, Term).
3. System computes gross tuition, laboratory, and institutional charges.
4. System creates `Invoice` and child `InvoiceLine` records with unique business IDs (`INV-...`).
5. Immutable `FinancialEvent` (`INVOICE_GENERATED`) is logged to the ledger.

### 3.2 Payment Allocation & Settlement
1. Payment received and recorded (`PaymentService.record_payment`).
2. Allocation engine matches outstanding invoice lines in statutory order (Tuition $\rightarrow$ Lab $\rightarrow$ Exam $\rightarrow$ Facilities).
3. `PaymentAllocation` records created; `amount_paid` and `outstanding_balance` updated atomically on `Invoice`.
4. Payment marked `COMPLETED`; `FinancialEvent` (`PAYMENT_ALLOCATED`) recorded.

### 3.3 Reconciliation & Anomaly Engine
1. Scheduled or on-demand trigger initiates `ReconciliationService`.
2. Cross-compares sum of invoice lines, payment allocations, and recorded ledger entries.
3. Flags discrepancies as `MISMATCHED` or `EXCEPTION` with variance calculation.
4. `AnomalyDetectionService` inspects the active dataset for non-compliant states (overpayments, duplicates, cap breaches) and records actionable records in `anomalies` table.

