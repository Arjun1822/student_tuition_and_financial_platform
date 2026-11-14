# Synthetic Data Generation & Reproducibility Audit

The platform includes a deterministic synthetic data generator (`backend/scripts/generate_data.py`) capable of generating realistic academic and financial datasets at multiple scales with mathematical parity and fixed-seed reproducibility.

---

## 1. Scale Specifications & Volumes

| Entity | Starter Scale Target | Starter Actual | Full Scale Target | Full Actual |
| :--- | :--- | :--- | :--- | :--- |
| **Students** | 100 | **100** | 10,000 | **10,000** |
| **Programs** | 20 | **20** | 20 | **20** |
| **Terms** | 4 | **4** | 4 | **4** |
| **Fee Schedules** | 80 | **80** | 80 | **80** |
| **Enrollments** | 300 | **300** | 30,000 | **30,000** |
| **Scholarship Schemes**| 5 | **5** | 5 | **5** |
| **Invoices** | 301 | **301** | 30,001 | **30,001\*** |
| **Invoice Lines** | 1,800 | **1,800** | 180,000 | **180,000** |
| **Scholarship Awards** | 150 | **150** | 15,000 | **15,000** |
| **Payments** | 500 | **500** | 50,000 | **50,000\*\*** |
| **Payment Allocations**| 1,251 | **1,251** | 125,000 | **125,000** |
| **Refunds** | 1 | **1** | 100 | **100** |
| **Financial Events** | 800 | **800** | 80,000 | **80,000** |
| **Audit Logs** | 100 | **100** | 10,000 | **10,000** |

*\*Note on Invoices (30,001)*: The baseline dataset contains exactly 30,000 legitimate billing invoices plus exactly 1 deliberately injected duplicate-invoice anomaly (`INV-STU-000001-2026-000002-DUP`).

*\*\*Note on Payments (50,000)*: Modeled across realistic multi-installment tuition payment schedules:
- 10% unpaid invoices (3,000 invoices $\rightarrow$ 0 payments).
- 4,000 single partial payments (4,000 payments).
- 23,000 two-installment payments (46,000 payments).
- Total: Exactly **50,000 valid payments**.

---

## 2. Deterministic Reproducibility

- **Fixed Random Seed**: `20261022`
- **Dependency Order**:
  1. `students` $\rightarrow$ 2. `programs` $\rightarrow$ 3. `terms` $\rightarrow$ 4. `fee_schedules` $\rightarrow$ 5. `enrollments` $\rightarrow$ 6. `scholarships` $\rightarrow$ 7. `invoices` $\rightarrow$ 8. `invoice_lines` $\rightarrow$ 9. `eligibilities` $\rightarrow$ 10. `payments` $\rightarrow$ 11. `payment_allocations` $\rightarrow$ 12. `refunds` $\rightarrow$ 13. `financial_events` $\rightarrow$ 14. `audit_logs` $\rightarrow$ 15. `ground_truth_anomalies`.
- **Reproducibility Audit (`backend/scripts/validate_reproducibility.py`)**:
  - Two completely independent generations produced **15/15 files with 100% identical SHA-256 checksums**:
    - `students.csv`: SHA-256 bit-identical
    - `programs.csv`: SHA-256 bit-identical
    - `terms.csv`: SHA-256 bit-identical
    - `fee_schedules.csv`: SHA-256 bit-identical
    - `enrollments.csv`: SHA-256 bit-identical
    - `invoices.csv`: SHA-256 bit-identical
    - `invoice_lines.csv`: SHA-256 bit-identical
    - `payments.csv`: SHA-256 bit-identical
    - `payment_allocations.csv`: SHA-256 bit-identical
    - `scholarships.csv`: SHA-256 bit-identical
    - `eligibilities.csv`: SHA-256 bit-identical
    - `refunds.csv`: SHA-256 bit-identical
    - `financial_events.csv`: SHA-256 bit-identical
    - `audit_logs.csv`: SHA-256 bit-identical
    - `ground_truth_anomalies.csv`: SHA-256 bit-identical
  - **Financial Parity**: Gross, Net, Paid, and Scholarship totals match to the exact cent across runs.

---

## 3. Ground-Truth Anomaly Separation

The generator creates a dedicated `ground_truth_anomalies.csv` file that documents each injected exception before the detection engine runs. This ensures unbiased evaluation with zero data contamination:

1. **Anomaly 1 (`OVERPAYMENT`)**: Payment exceeds invoice net outstanding balance.
2. **Anomaly 2 (`DUPLICATE_INVOICE`)**: Two distinct invoice records generated for the exact same student, term, and billing cycle.
3. **Anomaly 3 (`SCHOLARSHIP_EXCEEDS_CAP`)**: Award amount configured above statutory policy cap.
4. **Anomaly 4 (`INCORRECT_FEE_CALCULATION`)**: Invoice line total differs from configured fee schedule.
5. **Anomaly 5 (`ORPHAN_PAYMENT`)**: Payment with no corresponding invoice or enrollment association.

### Validation Script Execution
```powershell
python backend\scripts\validate_data.py --data-dir data/full
```
- **Referential Integrity**: PASSED
- **Financial Precision**: PASSED
- **Anomaly Detection**: Precision: 100.0%, Recall: 100.0%, F1 Score: 1.0
