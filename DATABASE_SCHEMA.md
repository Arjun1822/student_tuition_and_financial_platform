# Database Schema Documentation

The Student Financial Management Platform utilizes MySQL 8.0 with InnoDB storage engine to guarantee ACID transactions, strict referential integrity, and sub-millisecond query performance over high-volume financial datasets.

---

## 1. Entity-Relationship Overview

```
+---------------+        1:N       +------------------+
|   programs    |------------------|  fee_schedules   |
+---------------+                  +------------------+
       | 1:N                                |
       |                                    | 1:N
       v                                    v
+---------------+        1:N       +------------------+
|  enrollments  |------------------|     invoices     |
+---------------+                  +------------------+
       ^                                    |
       | 1:N                                | 1:N
+---------------+                           v
|   students    |                  +------------------+
+---------------+                  |  invoice_lines   |
       |                           +------------------+
       | 1:N                                ^
       v                                    | 1:N
+---------------+                  +------------------+
|   payments    |------------------| payment_allocations
+---------------+  1:N             +------------------+
       |
       | 1:N
       v
+---------------+
|    refunds    |
+---------------+

+-------------------+     1:N      +-------------------+
|   scholarships    |--------------|   eligibilities   |
+-------------------+              +-------------------+

+-------------------+              +-------------------+
|  financial_events |              |     anomalies     |
+-------------------+              +-------------------+
```

---

## 2. Table Specifications & Indexes

### 2.1 Core Identity & Academic Domain

#### `students`
- `id` (INT, PK, Auto-increment)
- `student_id` (VARCHAR(50), Unique, Index) — Business key `STU-XXXXXX`
- `user_id` (INT, FK `users.id`, Nullable)
- `first_name` (VARCHAR(100), Not Null)
- `last_name` (VARCHAR(100), Not Null)
- `email` (VARCHAR(255), Unique, Index)
- `phone` (VARCHAR(50), Nullable)
- `enrollment_year` (INT, Not Null)
- `gpa` (DECIMAL(4,2), Nullable)
- `family_income_category` (VARCHAR(50), Nullable)
- `status` (ENUM: `ACTIVE`, `INACTIVE`, `SUSPENDED`, `WITHDRAWN`, `GRADUATED`, Index)
- `created_at`, `updated_at` (DATETIME)

#### `programs`
- `id` (INT, PK, Auto-increment)
- `program_id` (VARCHAR(50), Unique, Index) — Business key `PRG-XXXXXX`
- `code` (VARCHAR(50), Unique, Index)
- `name` (VARCHAR(255), Not Null)
- `degree_level` (ENUM: `BACHELOR`, `MASTER`, `DOCTORATE`, `DIPLOMA`, `CERTIFICATE`)
- `duration_years` (INT, Not Null)
- `total_credits` (INT, Not Null)
- `status` (ENUM: `ACTIVE`, `INACTIVE`, `RETIRED`)
- `created_at`, `updated_at` (DATETIME)

#### `terms`
- `id` (INT, PK, Auto-increment)
- `term_id` (VARCHAR(50), Unique, Index) — Business key `TRM-XXXXXX`
- `name` (VARCHAR(100), Not Null)
- `academic_year` (VARCHAR(20), Not Null, Index)
- `start_date`, `end_date` (DATE, Not Null)
- `census_date` (DATE, Not Null)
- `status` (ENUM: `UPCOMING`, `ACTIVE`, `COMPLETED`, `CLOSED`)
- `created_at`, `updated_at` (DATETIME)

#### `fee_schedules`
- `id` (INT, PK, Auto-increment)
- `fee_schedule_id` (VARCHAR(50), Unique, Index) — Business key `FEE-XXXXXX`
- `program_id` (INT, FK `programs.id`, Not Null, Index)
- `term_id` (INT, FK `terms.id`, Not Null, Index)
- `tuition_fee` (DECIMAL(12,2), Not Null)
- `laboratory_fee` (DECIMAL(12,2), Not Null, Default 0.00)
- `library_fee` (DECIMAL(12,2), Not Null, Default 0.00)
- `examination_fee` (DECIMAL(12,2), Not Null, Default 0.00)
- `facilities_fee` (DECIMAL(12,2), Not Null, Default 0.00)
- `total_fee` (DECIMAL(12,2), Not Null)
- `currency` (VARCHAR(3), Default "INR")
- `is_active` (BOOLEAN, Default True)
- **Compound Index**: `ix_program_term_fee (program_id, term_id)`

#### `enrollments`
- `id` (INT, PK, Auto-increment)
- `enrollment_id` (VARCHAR(50), Unique, Index) — Business key `ENR-XXXXXX`
- `student_id` (INT, FK `students.id`, Not Null, Index)
- `program_id` (INT, FK `programs.id`, Not Null, Index)
- `term_id` (INT, FK `terms.id`, Not Null, Index)
- `enrollment_date` (DATE, Not Null)
- `academic_standing` (VARCHAR(50), Default "GOOD_STANDING")
- `status` (ENUM: `ACTIVE`, `DROPPED`, `WITHDRAWN`, `SUSPENDED`, `COMPLETED`, Index)
- **Compound Index**: `ix_enrollment_student_term (student_id, term_id)`

---

### 2.2 Financial & Billing Domain

#### `invoices`
- `id` (INT, PK, Auto-increment)
- `invoice_id` (VARCHAR(100), Unique, Index) — Business key `INV-...`
- `enrollment_id` (INT, FK `enrollments.id`, Not Null, Index)
- `student_id` (INT, FK `students.id`, Not Null, Index)
- `term_id` (INT, FK `terms.id`, Not Null, Index)
- `invoice_date`, `due_date` (DATE, Not Null)
- `gross_amount` (DECIMAL(12,2), Not Null)
- `scholarship_discount` (DECIMAL(12,2), Not Null, Default 0.00)
- `net_amount` (DECIMAL(12,2), Not Null)
- `amount_paid` (DECIMAL(12,2), Not Null, Default 0.00)
- `outstanding_balance` (DECIMAL(12,2), Not Null)
- `currency` (VARCHAR(3), Default "INR")
- `status` (ENUM: `DRAFT`, `ISSUED`, `PARTIALLY_PAID`, `PAID`, `OVERDUE`, `CANCELLED`, `REFUNDED`, Index)
- `billing_cycle` (VARCHAR(50), Not Null, Index)
- **Compound Index**: `ix_invoice_enrollment_cycle (enrollment_id, billing_cycle)`

#### `invoice_lines`
- `id` (INT, PK, Auto-increment)
- `invoice_id` (INT, FK `invoices.id`, Not Null, Index)
- `line_item_type` (ENUM: `TUITION`, `LABORATORY`, `LIBRARY`, `EXAMINATION`, `FACILITIES`, `LATE_FEE`, `DISCOUNT`)
- `description` (VARCHAR(255), Not Null)
- `gross_amount` (DECIMAL(12,2), Not Null)
- `discount_amount` (DECIMAL(12,2), Not Null, Default 0.00)
- `net_amount` (DECIMAL(12,2), Not Null)
- `paid_amount` (DECIMAL(12,2), Not Null, Default 0.00)
- `priority_order` (INT, Not Null, Default 1) — Used for statutory allocation order

#### `payments`
- `id` (INT, PK, Auto-increment)
- `payment_id` (VARCHAR(50), Unique, Index) — Business key `PAY-XXXXXX`
- `student_id` (INT, FK `students.id`, Not Null, Index)
- `amount` (DECIMAL(12,2), Not Null)
- `allocated_amount` (DECIMAL(12,2), Not Null, Default 0.00)
- `unallocated_amount` (DECIMAL(12,2), Not Null)
- `payment_date` (DATETIME, Not Null)
- `payment_method` (ENUM: `BANK_TRANSFER`, `CREDIT_CARD`, `DEBIT_CARD`, `UPI`, `CHEQUE`, `CASH`, `NET_BANKING`, Index)
- `reference_number` (VARCHAR(100), Nullable)
- `status` (ENUM: `PENDING`, `COMPLETED`, `FAILED`, `REVERSED`, `REFUNDED`, Index)

#### `payment_allocations`
- `id` (INT, PK, Auto-increment)
- `allocation_id` (VARCHAR(50), Unique, Index) — Business key `ALC-XXXXXX`
- `payment_id` (INT, FK `payments.id`, Not Null, Index)
- `invoice_line_id` (INT, FK `invoice_lines.id`, Not Null, Index)
- `amount` (DECIMAL(12,2), Not Null)
- `allocated_at` (DATETIME, Not Null)

#### `refunds`
- `id` (INT, PK, Auto-increment)
- `refund_id` (VARCHAR(50), Unique, Index) — Business key `REF-XXXXXX`
- `payment_id` (INT, FK `payments.id`, Not Null, Index)
- `student_id` (INT, FK `students.id`, Not Null, Index)
- `invoice_id` (INT, FK `invoices.id`, Nullable)
- `amount` (DECIMAL(12,2), Not Null)
- `reason` (TEXT, Not Null)
- `status` (ENUM: `REQUESTED`, `APPROVED`, `PROCESSED`, `REJECTED`, Index)
- `requested_date`, `approved_date`, `processed_date` (DATETIME)

---

### 2.3 Scholarships, Audit & Reconciliation Domain

#### `scholarships`
- `id` (INT, PK, Auto-increment)
- `scholarship_id` (VARCHAR(50), Unique, Index) — Business key `SCH-XXXXXX`
- `name` (VARCHAR(255), Not Null)
- `scholarship_type` (ENUM: `MERIT`, `NEED_BASED`, `PROGRAM_SPECIFIC`, `ATHLETIC`, `SPECIAL`, Index)
- `percentage` (DECIMAL(5,2), Not Null)
- `max_amount` (DECIMAL(12,2), Not Null)
- `min_gpa` (DECIMAL(4,2), Nullable)
- `total_budget` (DECIMAL(12,2), Not Null)
- `awarded_amount` (DECIMAL(12,2), Not Null, Default 0.00)
- `status` (ENUM: `ACTIVE`, `INACTIVE`, `EXHAUSTED`, Index)
- `academic_year` (VARCHAR(20), Not Null, Index)

#### `eligibilities`
- `id` (INT, PK, Auto-increment)
- `eligibility_id` (VARCHAR(50), Unique, Index) — Business key `ELG-XXXXXX`
- `student_id` (INT, FK `students.id`, Not Null, Index)
- `scholarship_id` (INT, FK `scholarships.id`, Not Null, Index)
- `calculated_amount` (DECIMAL(12,2), Not Null)
- `approved_amount` (DECIMAL(12,2), Not Null, Default 0.00)
- `decision_reason` (TEXT, Not Null)
- `status` (ENUM: `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`, `APPLIED`, Index)

#### `financial_events`
- `id` (INT, PK, Auto-increment)
- `event_id` (VARCHAR(50), Unique, Index) — Business key `EVT-XXXXXX`
- `event_type` (ENUM: `INVOICE_GENERATED`, `PAYMENT_RECORDED`, `PAYMENT_ALLOCATED`, `PAYMENT_REVERSED`, `SCHOLARSHIP_APPLIED`, `REFUND_PROCESSED`, `LATE_FEE_ASSESSED`, Index)
- `entity_type` (VARCHAR(50), Not Null)
- `entity_id` (VARCHAR(50), Not Null)
- `amount` (DECIMAL(12,2), Nullable)
- `previous_state`, `new_state` (VARCHAR(50), Nullable)
- `metadata_json` (JSON, Nullable)
- **Compound Index**: `ix_fin_event_entity (entity_type, entity_id)`

#### `anomalies`
- `id` (INT, PK, Auto-increment)
- `anomaly_id` (VARCHAR(50), Unique, Index) — Business key `ANM-XXXXXX`
- `issue_type` (ENUM: `OVERPAYMENT`, `DUPLICATE_INVOICE`, `SCHOLARSHIP_EXCEEDS_CAP`, `INCORRECT_FEE_CALCULATION`, `ORPHAN_PAYMENT`, Index)
- `severity` (ENUM: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`, Index)
- `entity_type`, `entity_id` (VARCHAR(50), Not Null)
- `expected_value`, `actual_value` (DECIMAL(12,2), Nullable)
- `explanation` (TEXT, Not Null)
- `resolution_status` (ENUM: `OPEN`, `INVESTIGATING`, `RESOLVED`, `IGNORED`, Index)

#### `reconciliation_runs` & `reconciliation_results`
- `reconciliation_runs`: Track audit executions (`run_id`, `run_date`, `total_invoices`, `matched_count`, `mismatched_count`, `exception_count`, `status`).
- `reconciliation_results`: Granular line-item audit (`expected_amount`, `actual_amount`, `difference`, `status`, `exception_type`).
