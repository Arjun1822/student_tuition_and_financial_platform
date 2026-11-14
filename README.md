# Student Tuition, Scholarship, Payment & Financial Reconciliation Platform

An enterprise-grade, 3-tier financial management and reconciliation platform built with FastAPI, React, MySQL 8.0, and Docker. The platform handles the complete student financial lifecycle—from academic enrollment, fee schedule computation, and automatic invoice generation to institutional scholarship governance, payment allocations, immutable ledger tracking, multi-period reconciliation, and heuristic anomaly detection.

---

## Key Features

1. **Academic Structure & Student Management**:
   - Multi-degree academic programs, terms, and configurable fee schedules (tuition, laboratory, library, examination, facilities).
   - Student onboarding, unique business IDs (`STU-XXXXXX`), and status tracking.
2. **Billing Engine & Automated Invoicing**:
   - Enrollment-triggered invoice generation with line-item charge composition.
   - Statutory line-item priorities, automatic fee schedule binding, and real-time outstanding balance computation.
3. **Scholarships & Institutional Grants**:
   - Endowment fund governance with budget tracking (`SCH-XXXXXX`).
   - Criteria-based automated eligibility evaluation engine (GPA thresholds, family income categories, program restrictions).
   - Dual-state approval and disbursement workflow (`ELG-XXXXXX`).
4. **Payments & Cash Management**:
   - Multi-channel payment recording (`PAY-XXXXXX`) supporting Bank Transfer, UPI, Credit/Debit cards, Net Banking, and Cheque.
   - Deterministic line-item allocation engine matching statutory charge priorities.
   - Reversible payments with automatic invoice balance restoration and immutable audit log entries.
5. **Refunds & Term Withdrawals**:
   - Withdrawal refund claim intake with validation against refundable balances (`REF-XXXXXX`).
   - Multi-tier governance: `REQUESTED` $\rightarrow$ `APPROVED` $\rightarrow$ `PROCESSED`.
6. **Immutable Financial Event Ledger & Audit Trail**:
   - Append-only, immutable event-sourced audit log (`EVT-XXXXXX`) capturing financial events with before/after state deltas.
   - On-demand real-time student balance statements reconciling gross charges, fee waivers, collected payments, and net liabilities.
7. **Multi-Period Reconciliation Engine**:
   - Automated discrepancy auditing across invoice lines and ledger totals (`REC-XXXXXX`).
   - Granular exception classification (`MATCHED`, `MISMATCHED`, `EXCEPTION`).
8. **Heuristic Anomaly Detection**:
   - Real-time detection across 5 mandatory financial integrity scenarios: Overpayments, Duplicate Invoices, Scholarship Cap Violations, Fee Calculation Mismatches, and Orphan Payments.
   - Full lifecycle resolution tracking (`OPEN` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `RESOLVED`).
9. **Executive Analytics Dashboard**:
   - Real-time KPIs (Gross Invoiced, Realized Collections, Outstanding Balances, Waivers, Overdue Invoices).
   - Responsive Recharts visualizations for program liabilities, invoice status distributions, payment flows, and anomaly breakdowns.

---

## Technology Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic v2, PyMySQL, Uvicorn, Pytest.
- **Frontend**: React 18, Vite, Tailwind CSS, React Router v6, Axios, Recharts, Lucide React, Vitest.
- **Database**: MySQL 8.0 with InnoDB, Decimal(12,2) monetary precision, and strict foreign keys.
- **Containerization**: Docker Compose, Multi-stage Node/Nginx container, Python slim backend container.

---

## Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 20+ and npm
- MySQL Server 8.0 (running locally on port 3306)

### Backend Setup (Windows PowerShell)

```powershell
# Navigate to project root
cd C:\CandidateWorkspace

# Create and activate Python 3.12 virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

# Run database migrations / seed
python backend\scripts\seed_db.py

# Start FastAPI Uvicorn Server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be live at `http://127.0.0.1:8000` with interactive Swagger docs at `http://127.0.0.1:8000/docs`.

### Frontend Setup (Windows PowerShell)

```powershell
# Navigate to frontend directory
cd C:\CandidateWorkspace\frontend

# Install dependencies
npm install

# Run Vite dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## Docker Compose Deployment

To deploy the entire production stack in isolated containers:

```powershell
# Validate configuration
docker-compose config

# Build and start services
docker-compose up --build -d

# Check health and service logs
docker-compose ps
docker-compose logs -f
```

- **Frontend Application (Nginx)**: `http://localhost:80`
- **FastAPI API**: `http://localhost:8000`
- **Health Endpoint**: `http://localhost:8000/health`

---

## Automated Test Verification

### Backend Integration Tests (Pytest)
```powershell
$env:PYTHONPATH = "C:\CandidateWorkspace\backend"
.\.venv\Scripts\python.exe -m pytest backend\app\tests -v
```
*Result: 22 passed in 15.32s.*

### Frontend Component & Route Tests (Vitest)
```powershell
cd C:\CandidateWorkspace\frontend
npm run test
```
*Result: 12 passed across 3 test suites in 7.79s.*

### Production Build Verification
```powershell
cd C:\CandidateWorkspace\frontend
npm run build
```
*Result: Succeeded with code splitting (index: 260 kB, vendor-react: 164 kB, vendor-charts: 413 kB).*

---

## Documentation Index

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture, components, and data flow.
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Relational schema, tables, constraints, and indexes.
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md) - Detailed entity attributes and data types.
- [BUSINESS_RULES.md](BUSINESS_RULES.md) - Financial calculation logic, limits, and workflows.
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - REST API endpoints and request/response schemas.
- [TESTING.md](TESTING.md) - Automated test strategies and execution reports.
- [SYNTHETIC_DATA_GENERATION.md](SYNTHETIC_DATA_GENERATION.md) - Deterministic data generator and reproducibility.
- [RECONCILIATION_LOGIC.md](RECONCILIATION_LOGIC.md) - Financial reconciliation rules and discrepancy checks.
- [ANOMALY_DETECTION.md](ANOMALY_DETECTION.md) - Anomaly heuristics and resolution workflows.
- [DEPLOYMENT.md](DEPLOYMENT.md) - Docker and production configuration guides.
- [SECURITY.md](SECURITY.md) - Authentication, RBAC, input sanitization, and audit posture.
- [VALIDATION_REPORT.md](VALIDATION_REPORT.md) - Synthetic data verification and metric compliance.

