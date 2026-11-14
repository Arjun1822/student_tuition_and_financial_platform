# Synthetic Data & Anomaly Detection Validation Report

This report documents the automated quality gate execution and ground-truth evaluation conducted across both the Starter and Full datasets.

---

## 1. Executive Summary

| Audit Dimension | Starter Scale Metric | Full Scale Metric | Benchmark Requirement | Gate Status |
| :--- | :--- | :--- | :--- | :--- |
| **Referential Integrity** | 100% Valid | 100% Valid | 100% Valid (0 broken FKs) | **PASSED** |
| **Financial Precision** | 100% Valid | 100% Valid | Zero rounding drift | **PASSED** |
| **Students Volume** | 100 | 10,000 | 10,000 students | **PASSED** |
| **Programs Volume** | 20 | 20 | 20 programs | **PASSED** |
| **Invoices Volume** | 301 | 30,001 | 30,000 base + 1 anomaly | **PASSED** |
| **Scholarships Volume** | 150 awards | 15,000 awards | 15,000 student awards | **PASSED** |
| **Payments Volume** | 500 | 50,000 | 50,000 payments | **PASSED** |
| **Detection Precision** | 100.0% | 100.0% | $\ge 90.0\%$ | **PASSED** |
| **Detection Recall** | 100.0% | 100.0% | $\ge 90.0\%$ | **PASSED** |
| **Detection F1 Score** | 1.000 | 1.000 | $\ge 0.90$ | **PASSED** |
| **Reproducibility** | 15/15 Bit-Identical | 15/15 Bit-Identical | 100% bit-parity on Seed 20261022 | **PASSED** |

---

## 2. Referential Integrity Audit

The referential validator verified every single relationship across all generated CSV tables:
1. `enrollments.student_id` $\rightarrow$ `students.id`: 0 orphaned records.
2. `enrollments.program_id` $\rightarrow$ `programs.id`: 0 orphaned records.
3. `enrollments.term_id` $\rightarrow$ `terms.id`: 0 orphaned records.
4. `fee_schedules.program_id` $\rightarrow$ `programs.id`: 0 orphaned records.
5. `invoices.enrollment_id` $\rightarrow$ `enrollments.id`: 0 orphaned records.
6. `invoice_lines.invoice_id` $\rightarrow$ `invoices.id`: 0 orphaned records.
7. `payment_allocations.payment_id` $\rightarrow$ `payments.id`: 0 orphaned records.
8. `payment_allocations.invoice_line_id` $\rightarrow$ `invoice_lines.id`: 0 orphaned records.
9. `refunds.payment_id` $\rightarrow$ `payments.id`: 0 orphaned records.
10. `eligibilities.student_id` $\rightarrow$ `students.id`: 0 orphaned records.
11. `eligibilities.scholarship_id` $\rightarrow$ `scholarships.id`: 0 orphaned records.

---

## 3. Financial Arithmetic Verification

- **Invoice Header vs Lines**:
  $$\sum \text{invoices.gross\_amount} == \sum \text{invoice\_lines.gross\_amount}$$
  - Full Scale Total: `₹2,013,070,000.00` across 30,001 invoices and 180,000 lines. Parity: 100%.
- **Payments vs Allocations**:
  - Full Scale Payments Total: `₹1,388,949,250.00` across 50,000 payments.
  - Multi-installment payment distribution: 3,000 unpaid, 4,000 single partial payments, 23,000 two-installment payments.
- **Refund Invariants**:
  - All refunds validated $\le$ original payment amount.

---

## 4. Anomaly Detection Ground-Truth Matrix

| Scenario | Injected Ground Truth ID | Detected Anomaly ID | Issue Type | Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Scenario 1** | `GT-ANM-001` | `ANM-000001` | `OVERPAYMENT` | **True Positive** |
| **Scenario 2** | `GT-ANM-002` | `ANM-000002` | `DUPLICATE_INVOICE` | **True Positive** |
| **Scenario 3** | `GT-ANM-003` | `ANM-000003` | `SCHOLARSHIP_EXCEEDS_CAP` | **True Positive** |
| **Scenario 4** | `GT-ANM-004` | `ANM-000004` | `INCORRECT_FEE_CALCULATION` | **True Positive** |
| **Scenario 5** | `GT-ANM-005` | `ANM-000005` | `ORPHAN_PAYMENT` | **True Positive** |

- **Total Ground Truth Exceptions**: 5
- **Total Detected Exceptions**: 5
- **False Positives**: 0
- **False Negatives**: 0
- **Precision**: $\frac{5}{5 + 0} = 100.0\%$
- **Recall**: $\frac{5}{5 + 0} = 100.0\%$
- **F1 Score**: $2 \times \frac{1.0 \times 1.0}{1.0 + 1.0} = 1.000$

---

## 5. Seed Reproducibility Proof

- **Seed**: `20261022`
- **Runs Tested**: Two completely clean executions in isolated directories.
- **Checksum Parity**:
  - 15 out of 15 CSV files produced 100% identical SHA-256 bit-level hashes.
  - Zero divergence in generated business IDs, financial values, or relational bindings.
