# Data Dictionary

This document details the operational data dictionary, attribute specifications, valid ranges, nullability, and primary business definitions across the platform.

---

## 1. Primary Business Entities

| Table | Attribute | Type | Nullable | Description / Business Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **users** | `id` | INT | NO | Surrogate primary key. |
| | `username` | VARCHAR(50) | NO | Unique login username. |
| | `email` | VARCHAR(255) | NO | Unique email address. |
| | `password_hash`| VARCHAR(255) | NO | Bcrypt-hashed password. |
| | `role` | ENUM | NO | `LEARNER`, `INSTRUCTOR`, `ACADEMIC_ADMIN`, `SUPPORT_STAFF`, `PLATFORM_ADMIN`. |
| | `is_active` | BOOLEAN | NO | Account active status flag. |
| **students** | `student_id` | VARCHAR(50) | NO | Deterministic key `STU-000001` to `STU-010000`. |
| | `gpa` | DECIMAL(4,2)| YES | Cumulative GPA on 0.00 to 10.00 scale. |
| | `family_income_category` | VARCHAR(50) | YES | Economic classification (`EWS`, `LOW`, `MIDDLE`, `HIGH`). |
| | `status` | ENUM | NO | Academic status (`ACTIVE`, `INACTIVE`, `SUSPENDED`, `WITHDRAWN`, `GRADUATED`). |
| **programs** | `program_id` | VARCHAR(50) | NO | Unique business key `PRG-000001` to `PRG-000020`. |
| | `code` | VARCHAR(50) | NO | Academic curriculum abbreviation (e.g. `CS-BTECH`, `EE-MTECH`). |
| | `degree_level` | ENUM | NO | Qualification tier (`BACHELOR`, `MASTER`, `DOCTORATE`, `DIPLOMA`, `CERTIFICATE`). |
| | `duration_years`| INT | NO | Duration in academic years (1 to 5). |
| **fee_schedules** | `fee_schedule_id`| VARCHAR(50)| NO | Unique schedule identifier `FEE-XXXXXX`. |
| | `tuition_fee` | DECIMAL(12,2)| NO | Base semester tuition fee. |
| | `laboratory_fee`| DECIMAL(12,2)| NO | Practical lab surcharge. |
| | `library_fee` | DECIMAL(12,2)| NO | Library and academic resource charge. |
| | `examination_fee`| DECIMAL(12,2)| NO | Term examination and assessment fee. |
| | `facilities_fee`| DECIMAL(12,2)| NO | Campus infrastructure charge. |
| | `total_fee` | DECIMAL(12,2)| NO | Calculated sum of all constituent fee items. |
| **enrollments** | `enrollment_id`| VARCHAR(50) | NO | Unique enrollment token `ENR-XXXXXX`. |
| | `academic_standing`| VARCHAR(50)| NO | Standing status (`GOOD_STANDING`, `PROBATION`, `HONORS`). |
| | `status` | ENUM | NO | Lifecycle status (`ACTIVE`, `DROPPED`, `WITHDRAWN`, `COMPLETED`). |
| **invoices** | `invoice_id` | VARCHAR(100)| NO | Deterministic ID `INV-STU-XXXXXX-YYYY-ZZZZZZ`. |
| | `gross_amount` | DECIMAL(12,2)| NO | Total charges before scholarships/discounts. |
| | `scholarship_discount`| DECIMAL(12,2)| NO | Applied institutional scholarship reduction. |
| | `net_amount` | DECIMAL(12,2)| NO | `gross_amount - scholarship_discount`. |
| | `amount_paid` | DECIMAL(12,2)| NO | Cumulative payments allocated to invoice lines. |
| | `outstanding_balance`| DECIMAL(12,2)| NO | `net_amount - amount_paid`. Minimum 0.00. |
| | `billing_cycle`| VARCHAR(50) | NO | Semantic cycle string (e.g. `2026-FALL`). |
| | `status` | ENUM | NO | `DRAFT`, `ISSUED`, `PARTIALLY_PAID`, `PAID`, `OVERDUE`, `CANCELLED`, `REFUNDED`. |
| **payments** | `payment_id` | VARCHAR(50) | NO | Deterministic receipt key `PAY-XXXXXX`. |
| | `amount` | DECIMAL(12,2)| NO | Tendered transaction amount. |
| | `allocated_amount`| DECIMAL(12,2)| NO | Amount disbursed to invoice line items. |
| | `unallocated_amount`| DECIMAL(12,2)| NO | Excess or pending credit balance. |
| | `payment_method`| ENUM | NO | `BANK_TRANSFER`, `CREDIT_CARD`, `DEBIT_CARD`, `UPI`, `CHEQUE`, `CASH`, `NET_BANKING`. |
| | `status` | ENUM | NO | Settlement state (`PENDING`, `COMPLETED`, `FAILED`, `REVERSED`, `REFUNDED`). |
| **refunds** | `refund_id` | VARCHAR(50) | NO | Deterministic refund token `REF-XXXXXX`. |
| | `amount` | DECIMAL(12,2)| NO | Disbursed refund amount. |
| | `status` | ENUM | NO | Approval stage (`REQUESTED`, `APPROVED`, `PROCESSED`, `REJECTED`). |
| **scholarships** | `scholarship_id`| VARCHAR(50)| NO | Endowment key `SCH-XXXXXX`. |
| | `percentage` | DECIMAL(5,2) | NO | Percentage discount (0.00 to 100.00). |
| | `max_amount` | DECIMAL(12,2)| NO | Monetary cap per award. |
| | `total_budget` | DECIMAL(12,2)| NO | Allocated institutional fund pool. |
| | `awarded_amount`| DECIMAL(12,2)| NO | Cumulative approved disbursements. |
| **financial_events**| `event_id` | VARCHAR(50) | NO | Immutable audit ledger ID `EVT-XXXXXX`. |
| | `event_type` | ENUM | NO | `INVOICE_GENERATED`, `PAYMENT_RECORDED`, `PAYMENT_ALLOCATED`, `PAYMENT_REVERSED`, `SCHOLARSHIP_APPLIED`, `REFUND_PROCESSED`, `LATE_FEE_ASSESSED`. |
| | `metadata_json`| JSON | YES | Machine-readable context, payload parameters, and state delta. |
| **anomalies** | `anomaly_id` | VARCHAR(50) | NO | Unique anomaly identifier `ANM-XXXXXX`. |
| | `issue_type` | ENUM | NO | `OVERPAYMENT`, `DUPLICATE_INVOICE`, `SCHOLARSHIP_EXCEEDS_CAP`, `INCORRECT_FEE_CALCULATION`, `ORPHAN_PAYMENT`. |
| | `severity` | ENUM | NO | Risk classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). |
| | `resolution_status`| ENUM | NO | Remediation state (`OPEN`, `INVESTIGATING`, `RESOLVED`, `IGNORED`). |

---

## 2. Common Enums & Domains

- **Currency**: ISO-4217 standard (`INR`, Indian Rupee).
- **Date Formats**: ISO-8601 (`YYYY-MM-DD` for dates, `YYYY-MM-DDTHH:MM:SSZ` for UTC timestamps).
- **Rounding Rule**: Standard banker's rounding (`ROUND_HALF_UP`) with 2 decimal places.
