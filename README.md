# Student Tuition, Scholarship, Payment & Financial Reconciliation Platform

An enterprise-grade, 3-tier financial management, accounting, and reconciliation platform built with FastAPI, React 18, MySQL 8.0, and Docker. The platform handles the complete institutional student financial lifecycle—including student onboarding, program fee structure scheduling, automated invoice generation, scholarship eligibility evaluation and awards governance, multi-channel payment allocation, payment reversals, student refunds, immutable event-sourced financial audit trails, multi-period balance reconciliation, heuristic anomaly detection, and real-time executive financial analytics.

**GitHub Repository**: [https://github.com/Arjun1822/student_tuition_and_financial_platform](https://github.com/Arjun1822/student_tuition_and_financial_platform)

---

## 1. Key Features

1. **Academic Structure & Student Management**:
   - Multi-degree academic programs (Undergraduate, Postgraduate, Doctorate), academic terms, and granular fee schedule composition (Tuition, Laboratory, Library, Examination, Facilities).
   - Student profile onboarding with deterministic business identifiers (`STU-XXXXXX`) and active lifecycle status tracking.

2. **Automated Billing & Invoice Generation**:
   - Automated invoice generation triggered by term enrollment, composing statutory line-item charges.
   - Dynamic calculation of gross amounts, statutory line priorities, fee schedule bindings, and real-time outstanding balances.
   - Batch assessment of late fees for overdue balances exceeding statutory grace periods.

3. **Scholarships & Institutional Grants**:
   - Institutional scholarship endowment governance with total and remaining budget enforcement (`SCH-XXXXXX`).
   - Criteria-based automated eligibility evaluation engine assessing cumulative GPA thresholds, family income categories, and eligible degree programs.
   - Multi-tier award governance: evaluation, approval/rejection workflows, and automated invoice tuition discount application (`ELG-XXXXXX`).

4. **Payments, Allocations & Reversals**:
   - Multi-channel payment recording (`PAY-XXXXXX`) supporting Bank Transfer, UPI, Credit Card, Debit Card, Net Banking, and Cheque.
   - Deterministic FIFO line-item payment allocation engine prioritizing statutory charge orders.
   - Strict allocation boundaries preventing overpayment on individual lines with automated credit balance tracking.
   - Full payment reversal workflows restoring invoice balances and recording ledger events.

5. **Refunds & Term Withdrawals**:
   - Refund claim intake and lifecycle governance (`REF-XXXXXX`): `REQUESTED` $\rightarrow$ `APPROVED` $\rightarrow$ `PROCESSED`.
   - Strict validation preventing refund amounts from exceeding actual refundable settled balances.

6. **Immutable Financial Event Ledger & Balance Calculation**:
   - Append-only, event-sourced audit trail (`EVT-XXXXXX`) capturing financial state transitions (`INVOICE_GENERATED`, `PAYMENT_ALLOCATED`, `PAYMENT_REVERSED`, `SCHOLARSHIP_APPLIED`, `REFUND_PROCESSED`).
   - Real-time student balance statements dynamically reconciling total billed debits, scholarship waivers, collected payments, and net liabilities.

7. **Multi-Period Financial Reconciliation Engine**:
   - Automated reconciliation engine (`REC-XXXXXX`) auditing expected balances against recorded transaction totals.
   - Discrepancy detection with classification into `MATCHED`, `MISMATCHED`, and `EXCEPTION` outcomes.

8. **Heuristic Anomaly Detection**:
   - Rule-based detection across 5 ground-truth financial integrity scenarios:
     1. `PAYMENT_OVER_ALLOCATED`: Payment allocated beyond the actual payment amount.
     2. `SCHOLARSHIP_EXCEEDS_FEES`: Scholarship award exceeds eligible tuition charges.
     3. `DUPLICATE_INVOICE`: Duplicate invoice generation for the same student, enrollment, and term.
     4. `REFUND_EXCEEDS_PAID`: Refund exceeds the net amount actually paid and settled, considering prior refunds.
     5. `BALANCE_MISMATCH`: Stored invoice/student balance disagrees with ledger-derived arithmetic.
   - Complete anomaly investigation and resolution lifecycle tracking (`OPEN` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `RESOLVED`).

9. **Executive Analytics Dashboard & Reporting**:
   - Real-time executive KPIs: Gross Invoiced, Total Scholarships Awarded, Net Collectible, Total Collections, Realized Collection Rate, and Outstanding Balance.
   - Interactive Recharts visualizations: Monthly Collection Trends, Program Revenue Breakdown, Invoice Aging Distributions, Payment Method Splits, and Anomaly Severity Distributions.

---

## 2. Technology Stack

- **Presentation Tier**: React 18, Vite 5, Tailwind CSS 3, React Router v6 (with v7 future flags enabled), Axios, Recharts, Lucide React, React Hook Form, Zod.
- **Application Tier**: Python 3.12, FastAPI, SQLAlchemy 2.0 (ORM), Pydantic v2, PyMySQL, Uvicorn, Python-Jose (JWT), Passlib (Bcrypt).
- **Data Tier**: MySQL 8.0 with InnoDB engine, Decimal(12,2) fixed-point monetary precision, composite B-tree indexes, and explicit foreign key constraints.
- **Testing & Tooling**: Pytest, Pytest-Asyncio, HTTPX, Vitest, React Testing Library, JSDOM.
- **Deployment & Orchestration**: Docker, Docker Compose, Nginx reverse proxy (Alpine), multi-stage container builds.

---

## 3. Architecture Overview

The platform implements a strict 3-tier enterprise architecture separating presentation, business domain logic, and persistent storage:

```
+-----------------------------------------------------------------------+
|                             PRESENTATION TIER                         |
|  React 18 + Vite SPA  |  Tailwind CSS  |  Recharts  |  React Router   |
|  - Academic Operations (Students, Programs, Enrollments, Invoices)    |
|  - Financial Management (Scholarships, Payments, Refunds)             |
|  - Audit & Governance (Ledger, Reconciliation, Anomalies, Reports)    |
+-----------------------------------+-----------------------------------+
                                    |
                                    | HTTP / REST (JWT Bearer Auth)
                                    v
+-----------------------------------+-----------------------------------+
|                              BUSINESS TIER                            |
|             FastAPI Application (Python 3.12 + Pydantic v2)           |
|                                                                       |
|  [ API Endpoints & Routers ]                                          |
|   - Authentication & Role-Based Access Control (RBAC)                 |
|   - Academic Resources & Invoices Router                              |
|   - Financial Lifecycle & Ledger Routers                              |
|                                                                       |
|  [ Business Domain Services ]                                         |
|   - InvoiceGenerationService    - ScholarshipEligibilityService       |
|   - PaymentAllocationService    - RefundManagementService             |
|   - BalanceCalculationService   - ReconciliationAuditEngine           |
|   - AnomalyDetectionService     - AuditService                        |
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
|  - Decimal(12,2) Fixed-Precision Monetary Calculations                |
|  - Compound & B-Tree Indexes on Foreign Keys & Query Paths            |
|  - Append-Only Immutable Event & Audit Logs                           |
+-----------------------------------------------------------------------+
```

### Relational Schema (19 SQLAlchemy Models)
1. **Security & Identity**: `User`, `Role`
2. **Academic Structure**: `Student`, `Program`, `Term`, `FeeSchedule`, `Enrollment`
3. **Billing & Invoices**: `Invoice`, `InvoiceLine`
4. **Scholarships**: `Scholarship`, `Eligibility`
5. **Payments & Cash**: `Payment`, `PaymentAllocation`
6. **Refunds**: `Refund`
7. **Accounting & Audit**: `FinancialEvent`, `AuditLog`
8. **Reconciliation**: `ReconciliationRun`, `ReconciliationResult`
9. **Integrity**: `Anomaly`

---

## 4. Project Folder Structure

```
CandidateWorkspace/
├── .env.example                # Template for environment configuration
├── .gitignore                  # Git exclusion rules
├── docker-compose.yml          # Multi-container production deployment definition
├── README.md                   # Consolidated project documentation
├── backend/
│   ├── Dockerfile              # Backend container build definition
│   ├── requirements.txt        # Python backend dependencies
│   ├── alembic/                # Database migration scripts
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint and middleware configuration
│   │   ├── api/
│   │   │   ├── dependencies.py # Auth dependencies, current user, RoleChecker
│   │   │   └── v1/
│   │   │       ├── api.py      # Unified v1 API router
│   │   │       └── endpoints/  # 17 domain endpoint controllers
│   │   ├── core/
│   │   │   ├── config.py       # Pydantic v2 application settings
│   │   │   ├── database.py     # SQLAlchemy engine and session factory
│   │   │   ├── permissions.py  # UserRole enum and role verification
│   │   │   └── security.py     # JWT token and bcrypt password utilities
│   │   ├── models/             # 19 SQLAlchemy declarative models
│   │   ├── repositories/       # 13 database repository classes
│   │   ├── schemas/            # Pydantic request and response schemas
│   │   ├── services/           # Financial business domain services
│   │   └── tests/              # 22 automated Pytest integration suites
│   └── scripts/
│       ├── generate_data.py    # Deterministic synthetic data generator
│       ├── seed_db.py          # Database seeding script
│       ├── validate_data.py    # Target dataset and integrity validator
│       └── validate_reproducibility.py # Bit-identical SHA-256 reproducibility check
├── data/
│   ├── starter/                # 100-student starter dataset
│   └── full/                   # 10,000-student, 50,000-payment full dataset
└── frontend/
    ├── Dockerfile              # Frontend multi-stage Node/Nginx build definition
    ├── nginx.conf              # Production Nginx reverse-proxy configuration
    ├── package.json            # Node.js dependencies and npm scripts
    ├── vite.config.js          # Vite configuration with chunk code-splitting
    └── src/
        ├── App.jsx             # Root component with routing and future flags
        ├── main.jsx            # Application mount point
        ├── api/                # Axios API client and domain service modules
        ├── components/         # Reusable UI components (Modal, StatusBadge, Pagination)
        ├── context/            # AuthContext for session management
        ├── pages/              # 15 domain and financial views
        └── test/               # 12 Vitest automated test suites
```

---

## 5. Prerequisites

- **Python**: 3.12 or higher
- **Node.js**: 20.x or 22.x LTS (with `npm`)
- **MySQL**: 8.0 (running locally on port 3306 or via Docker)
- **Docker & Docker Compose**: (Optional, for containerized deployment)

---

## 6. Local Development Setup

### Backend Setup (Windows PowerShell)

```powershell
# 1. Navigate to workspace root
cd C:\CandidateWorkspace

# 2. Create and activate virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install backend dependencies
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

# 4. Configure environment variables (copy from template)
Copy-Item .env.example .env

# 5. Initialize database tables and seed test data
python backend\scripts\seed_db.py

# 6. Start the FastAPI development server
$env:PYTHONPATH = "C:\CandidateWorkspace\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The FastAPI application will be accessible at:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`
- **Health Check Endpoint**: `http://127.0.0.1:8000/health`

### Frontend Setup (Windows PowerShell)

```powershell
# 1. Navigate to frontend directory
cd C:\CandidateWorkspace\frontend

# 2. Install dependencies
npm install

# 3. Start the Vite development server
npm run dev
```

The frontend application will be live at:
- **Application URL**: `http://localhost:5173`

---

## 7. MySQL Configuration (Environment Variables)

All database connection parameters are configurable via standard environment variables:

| Variable Name | Description | Default Value |
|---|---|---|
| `MYSQL_HOST` | Database host hostname or IP | `localhost` (or `mysql` in Docker) |
| `MYSQL_PORT` | Database service port | `3306` |
| `MYSQL_USER` | Database username | `root` |
| `MYSQL_PASSWORD` | Database user password | Set in `.env` |
| `MYSQL_DATABASE` | Target database schema name | `student_finance_db` |
| `SECRET_KEY` | Secret key used for signing JWT tokens | Set in `.env` |
| `ALGORITHM` | JWT cryptographic signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifespan in minutes | `60` |

---

## 8. Docker Deployment Instructions

The complete three-tier platform can be orchestrated using Docker Compose:

```powershell
# 1. Validate Docker Compose configuration
docker-compose config

# 2. Build images and start all containers in detached mode
docker-compose up --build -d

# 3. Verify service health and container status
docker-compose ps

# 4. Inspect container logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql

# 5. Tear down containers and networks
docker-compose down
```

### Docker Service Endpoints
- **Frontend SPA (Nginx Reverse Proxy)**: `http://localhost:80`
- **FastAPI Backend**: `http://localhost:8000`
- **API Swagger Documentation**: `http://localhost:8000/docs`
- **MySQL Database Server**: `localhost:3306`

---

## 9. API Documentation & Endpoint Overview

Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

### Core API Route Summary
| Route Prefix | Category | Key Operations |
|---|---|---|
| `/api/v1/auth` | Authentication | `POST /login`, `POST /login-json`, `GET /me` |
| `/api/v1/students` | Students | `GET /`, `POST /`, `GET /{id}`, `PUT /{id}` |
| `/api/v1/programs` | Programs | `GET /`, `POST /`, `GET /{id}`, `PUT /{id}` |
| `/api/v1/terms` | Terms | `GET /`, `POST /`, `GET /{id}` |
| `/api/v1/fee-schedules`| Fee Schedules | `GET /`, `POST /`, `GET /{id}`, `PUT /{id}` |
| `/api/v1/enrollments` | Enrollments | `GET /`, `POST /`, `GET /{id}`, `POST /{id}/cancel`, `POST /{id}/withdraw` |
| `/api/v1/invoices` | Invoicing | `GET /`, `POST /generate`, `GET /{id}`, `POST /{id}/cancel` |
| `/api/v1/scholarships` | Scholarships | `GET /`, `POST /`, `GET /{id}`, `PUT /{id}`, `POST /evaluate` |
| `/api/v1/eligibilities`| Awards | `GET /`, `GET /{id}`, `POST /{id}/approve`, `POST /{id}/reject` |
| `/api/v1/payments` | Payments | `GET /`, `POST /`, `GET /{id}`, `POST /{id}/allocate`, `POST /{id}/reverse` |
| `/api/v1/payment-allocations` | Allocations | `GET /` |
| `/api/v1/refunds` | Refunds | `GET /`, `POST /`, `GET /{id}`, `POST /{id}/approve`, `POST /{id}/process`, `POST /{id}/reject` |
| `/api/v1/ledger` | Event Ledger | `GET /events`, `GET /students/{id}/statement`, `POST /invoices/{id}/late-fee` |
| `/api/v1/reconciliation` | Reconciliation | `POST /run`, `GET /runs`, `GET /runs/{id}`, `GET /runs/{id}/results` |
| `/api/v1/anomalies` | Anomalies | `GET /`, `POST /scan`, `GET /{id}`, `POST /{id}/resolve` |
| `/api/v1/reports` | Reports | `GET /dashboard` |

---

## 10. Automated Test Execution

### Backend Pytest Suite
```powershell
# Run all backend tests
$env:PYTHONPATH = "C:\CandidateWorkspace\backend"
.\.venv\Scripts\python.exe -m pytest backend/app/tests -v
```
- **Total Tests**: 23 tests across 4 test modules (`test_database.py`, `test_health_async.py`, `test_milestone3.py`, `test_milestones4_5.py`).
- **Pass Rate**: 100% (23/23 passed).

### Frontend Vitest Suite
```powershell
# Run all frontend unit and integration tests
cd C:\CandidateWorkspace\frontend
npm run test
```
- **Total Tests**: 12 tests across 3 test suites (`App.test.jsx`, `DetailPages.test.jsx`, `FinancialPages.test.jsx`).
- **Pass Rate**: 100% (12/12 passed, 0 warnings).

### Frontend Production Build
```powershell
# Compile and bundle frontend for production
cd C:\CandidateWorkspace\frontend
npm run build
```
- **Build Output**: Clean bundle with code-splitting (`dist/assets/index.js`: ~260 kB, `vendor-react.js`: ~164 kB, `vendor-charts.js`: ~413 kB).

---

## 11. Synthetic Dataset Generation & Validation

The platform includes a deterministic synthetic data generation engine seeded for 100% reproducible test and audit datasets:

- **Random Seed**: `20261022`
- **Target Scale Options**:
  - `starter`: 100 students, 5 programs, 300 invoices, 150 scholarship awards, 500 payments.
  - `full`: 10,000 students, 20 programs, 30,001 invoices, 15,000 scholarship awards, 50,000 payments.

### Generation Commands
```powershell
# Generate starter dataset (exports CSV, JSON, and seed_data.sql)
python backend\scripts\generate_data.py --scale starter --seed 20261022 --export-dir data/starter

# Generate full dataset (exports CSV, JSON, and seed_data.sql)
python backend\scripts\generate_data.py --scale full --seed 20261022 --export-dir data/full
```

### Validation Commands
```powershell
# Validate starter dataset compliance
python backend\scripts\validate_data.py --data-dir data/starter

# Validate full dataset compliance
python backend\scripts\validate_data.py --data-dir data/full

# Verify bit-identical SHA-256 reproducibility across CSV, JSON, and SQL seed files
python backend\scripts\validate_reproducibility.py --scale starter --seed 20261022
```
- **Validation Results**: 100% compliance across primary/foreign keys, enum domains, date ordering, financial arithmetic, and anomaly evaluations.
- **Anomaly Detection Evaluation**: 100% Precision, 100% Recall, F1=1.0 across all 5 mandatory scenarios.
- **Reproducibility**: 100% bit-identical SHA-256 matching across all CSV, JSON, and SQL seed files.

---

## 12. Security Considerations & RBAC

1. **Authentication**:
   - Access tokens generated via `python-jose` using `HS256` symmetric signing with configurable expiration.
   - Passwords securely hashed with `bcrypt` via Passlib.
   - Protected API endpoints require `Authorization: Bearer <token>` headers.
2. **Role-Based Access Control (RBAC)**:
   - Configurable access tiers via `RoleChecker` and `require_permissions` dependencies:
     - `PLATFORM_ADMIN`: Universal administrator privileges across all academic, billing, financial, and audit endpoints.
     - `ACADEMIC_ADMIN`: Operational access to students, programs, fee schedules, terms, and enrollments.
     - `SUPPORT_STAFF`: Read and operational ticket assistance privileges.
     - `LEARNER`: Student self-service access to own invoices, payments, and balance statements.
   - Unauthorized access returns HTTP `403 Forbidden` preserving session context without unexpected logouts.
3. **Data Integrity & Auditability**:
   - Immutable financial event logging for all financial mutations.
   - Zero hardcoded credentials or secret keys committed to source control.
