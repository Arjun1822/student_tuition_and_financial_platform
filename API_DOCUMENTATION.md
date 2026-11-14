# REST API Documentation

The platform provides a modular, RESTful API mounted under the `/api/v1` namespace. All authenticated routes require a valid JWT token passed in the `Authorization` header: `Authorization: Bearer <TOKEN>`.

---

## 1. Authentication & Session Management

### `POST /api/v1/auth/login`
- **Description**: Authenticate user credentials and issue JWT access token.
- **Request (Form URL Encoded)**:
  - `username`: string
  - `password`: string
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "role": "PLATFORM_ADMIN"
  }
  ```

### `GET /api/v1/auth/me`
- **Description**: Retrieve current active user profile and roles.
- **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "username": "admin",
    "email": "admin@university.edu",
    "role": "PLATFORM_ADMIN"
  }
  ```

---

## 2. Students & Academic Structure

### `GET /api/v1/students/`
- **Query Parameters**: `page` (default 1), `page_size` (default 20), `status`, `search`.
- **Response (200 OK)**: Paginated list of students.

### `POST /api/v1/students/`
- **Request Body**: `StudentCreate` (`first_name`, `last_name`, `email`, `phone`, `enrollment_year`, `gpa`, `family_income_category`).
- **Response (201 Created)**: Created `StudentResponse`.

### `GET /api/v1/programs/` & `POST /api/v1/programs/`
- Management of degree curriculums and accreditation codes.

### `GET /api/v1/fee-schedules/` & `POST /api/v1/fee-schedules/`
- Management of term-specific fee schedules linking tuition, laboratory, library, exam, and facility fees.

### `GET /api/v1/enrollments/` & `POST /api/v1/enrollments/`
- Student term enrollments and registration lifecycle.

---

## 3. Invoices & Billing Engine

### `GET /api/v1/invoices/`
- **Query Parameters**: `page`, `page_size`, `student_id`, `term_id`, `status`.
- **Response (200 OK)**: Paginated list of invoices with gross, net, paid, and balance amounts.

### `GET /api/v1/invoices/{id}`
- **Description**: Full invoice detail including all child line items and payment allocations.

### `POST /api/v1/invoices/generate`
- **Request Body**: `{"enrollment_id": int, "notes": string}`
- **Description**: Evaluates fee schedule, generates invoice lines, applies eligible scholarships, and computes net balance.

### `POST /api/v1/invoices/{id}/cancel`
- **Request Body**: `{"reason": string}`
- **Description**: Voids invoice and updates ledger.

---

## 4. Scholarships & Institutional Aid

### `GET /api/v1/scholarships/` & `POST /api/v1/scholarships/`
- Manage endowment schemes, benefit percentages, caps, and fund budgets.

### `POST /api/v1/scholarships/evaluate`
- **Request Body**: `{"student_id": int, "term_id": int, "scholarship_ids": Optional[List[int]]}`
- **Description**: Evaluates student GPA, income, and enrollment against scholarship criteria.

### `GET /api/v1/eligibilities/`
- List evaluated student scholarship applications.

### `POST /api/v1/eligibilities/{id}/approve`
- **Request Body**: `{"approved_amount": Optional[Decimal], "notes": Optional[str]}`

### `POST /api/v1/eligibilities/{id}/reject`
- **Request Body**: `{"reason": str}`

---

## 5. Payments & Receipts

### `GET /api/v1/payments/`
- **Query Parameters**: `page`, `page_size`, `student_id`, `status`, `payment_method`.

### `POST /api/v1/payments/`
- **Request Body**: `PaymentCreate` (`student_id`, `amount`, `payment_method`, `reference_number`, `auto_allocate`, `invoice_id`).

### `POST /api/v1/payments/{id}/allocate`
- **Request Body**: `{"allocations": [{"invoice_line_id": int, "amount": Decimal}], "auto_allocate": bool}`

### `POST /api/v1/payments/{id}/reverse`
- **Request Body**: `{"reason": string}`
- **Description**: Restores line-item balances and records reversal event.

### `GET /api/v1/payment-allocations/`
- Query line-item allocation breakdowns by `payment_id` or `invoice_line_id`.

---

## 6. Refunds & Term Withdrawals

### `GET /api/v1/refunds/` & `POST /api/v1/refunds/`
- Intake of withdrawal and overpayment refund claims.

### `POST /api/v1/refunds/{id}/approve`
- Authorize refund request.

### `POST /api/v1/refunds/{id}/process`
- Execute disbursement to bank account, credit student ledger, and finalize record.

### `POST /api/v1/refunds/{id}/reject`
- Reject refund with justification.

---

## 7. Financial Ledger & Auditing

### `GET /api/v1/ledger/events`
- Query immutable append-only event stream filtered by `event_type`, `entity_type`, `entity_id`.

### `GET /api/v1/ledger/students/{student_id}/statement`
- Real-time comprehensive balance statement reconciling gross charges, scholarships, net collectible, payments, refunds, and all invoice balances.

### `POST /api/v1/ledger/invoices/{invoice_id}/late-fee`
- Assesses overdue penalty fee and posts debit to ledger.

---

## 8. Reconciliation & Anomaly Engine

### `POST /api/v1/reconciliation/run`
- **Request Body**: `{"term_id": Optional[int], "program_id": Optional[int], "notes": Optional[str]}`
- **Description**: Executes line-item reconciliation comparing invoice balances against ledger totals.

### `GET /api/v1/reconciliation/runs` & `GET /api/v1/reconciliation/runs/{id}/results`
- Retrieve reconciliation run histories and discrepancy line items.

### `GET /api/v1/anomalies/`
- Filter detected exceptions by `issue_type`, `severity`, `resolution_status`.

### `POST /api/v1/anomalies/scan`
- Triggers active scan of all financial integrity heuristic rules.

### `POST /api/v1/anomalies/{id}/resolve`
- **Request Body**: `{"resolution_status": "RESOLVED", "resolution_notes": string}`

---

## 9. Executive Reporting & Analytics

### `GET /api/v1/reports/dashboard`
- **Description**: Returns consolidated executive KPIs and pre-aggregated chart payloads for Recharts visualizations.
- **Payload**:
  - `kpis`: `total_students`, `active_enrollments`, `total_invoice_value`, `scholarships_awarded`, `payments_collected`, `outstanding_balance`, `overdue_invoices`, `refunds_processed`, `unresolved_anomalies`.
  - `charts`: `invoices_by_status`, `payments_by_status`, `anomalies_by_type`, `outstanding_by_program`.

