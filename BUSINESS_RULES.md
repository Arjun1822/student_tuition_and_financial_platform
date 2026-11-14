# Financial Business Rules & Calculation Specifications

This document outlines the strict business logic, validation boundaries, and financial arithmetic implemented across the platform.

---

## 1. Invoice & Billing Rules

### 1.1 Gross Amount Calculation
- The gross charge of an invoice is computed as the sum of all applicable line items defined in the active program fee schedule:
  $$\text{Gross Amount} = \text{Tuition} + \text{Laboratory} + \text{Library} + \text{Examination} + \text{Facilities}$$
- Each charge component is instantiated as an independent `InvoiceLine` with an assigned statutory priority:
  1. `TUITION` (Priority 1)
  2. `LABORATORY` (Priority 2)
  3. `LIBRARY` (Priority 3)
  4. `EXAMINATION` (Priority 4)
  5. `FACILITIES` (Priority 5)

### 1.2 Scholarship Discount & Net Amount
- Approved scholarship awards apply directly to eligible tuition fees.
- The net payable amount is strictly bounded:
  $$\text{Net Amount} = \max(0.00, \text{Gross Amount} - \text{Scholarship Discount})$$
- The scholarship discount cannot exceed the invoice gross charge.

### 1.3 Invoice Status Transitions
- `DRAFT`: Initial state prior to official release.
- `ISSUED`: Published to student ledger; payable.
- `PARTIALLY_PAID`: $0.00 < \text{Amount Paid} < \text{Net Amount}$.
- `PAID`: $\text{Amount Paid} \ge \text{Net Amount}$ and $\text{Outstanding Balance} = 0.00$.
- `OVERDUE`: Current date exceeds `due_date` with $\text{Outstanding Balance} > 0.00$.
- `CANCELLED`: Voided prior to payment; outstanding balance set to $0.00$.
- `REFUNDED`: Entire settled amount reversed or returned upon withdrawal.

---

## 2. Scholarship Eligibility & Award Governance

### 2.1 Award Calculation Formula
$$\text{Calculated Award} = \min\left(\text{Max Cap}, \text{Eligible Fee Amount} \times \frac{\text{Percentage}}{100}\right)$$

### 2.2 Qualification Criteria
- **Merit Scholarships**: Requires student cumulative GPA $\ge \text{min\_gpa}$ threshold (e.g. GPA $\ge 8.50$).
- **Need-Based Scholarships**: Evaluates `family_income_category` matching economic thresholds (`EWS` or `LOW`).
- **Program-Specific Scholarships**: Verified against `eligible_programs` array.
- **Budgetary Constraints**: Total awarded funds across a scholarship scheme cannot exceed `total_budget`. When $\text{awarded\_amount} \ge \text{total\_budget}$, status automatically transitions to `EXHAUSTED`.

---

## 3. Payment Processing & Line-Item Allocation

### 3.1 Allocation Order of Precedence
When a payment is recorded with `auto_allocate=True`, funds are disbursed sequentially across outstanding invoice lines:
1. Outstanding Tuition charges (Priority 1).
2. Outstanding Laboratory charges (Priority 2).
3. Outstanding Library charges (Priority 3).
4. Outstanding Examination charges (Priority 4).
5. Outstanding Facilities charges (Priority 5).
6. Outstanding Late Fees (Priority 6).

### 3.2 Allocation Boundaries
- An invoice line cannot receive an allocation exceeding its remaining balance:
  $$\text{Allocated to Line}_i \le \text{Net Amount}_i - \text{Paid Amount}_i$$
- Total allocations for a payment cannot exceed the total payment amount:
  $$\sum \text{Allocations} \le \text{Payment Amount}$$
- Any unallocated funds are preserved in `unallocated_amount` as a student credit balance.

### 3.3 Payment Reversal
- When a payment is reversed (`POST /api/v1/payments/{id}/reverse`):
  1. The payment status changes to `REVERSED`.
  2. All child `PaymentAllocation` records are decremented from their respective invoice lines.
  3. The parent `Invoice.amount_paid` is reduced and `Invoice.outstanding_balance` is restored.
  4. An immutable `PAYMENT_REVERSED` event is logged to the financial ledger.

---

## 4. Late Fees & Interest Assessment

- Assessed on invoices with status `OVERDUE` where current date exceeds `due_date + grace_period` (default: 15 grace days).
- Formula:
  $$\text{Late Fee} = \min\left(\text{Max Cap}, \max(\text{Fixed Fee}, \text{Outstanding Balance} \times \text{Rate})\right)$$
- Default parameters: $\text{Fixed Fee} = ₹500.00$, $\text{Max Cap} = ₹2,500.00$.
- Assessment generates an additional `InvoiceLine` with type `LATE_FEE` and records a ledger event.

---

## 5. Refund & Term Withdrawal Policy

- Refund claims are linked to completed payments (`REFUND_REQUESTED`).
- Validation limits:
  $$\text{Refund Amount} \le \text{Payment Amount} - \text{Previously Refunded Amount}$$
- Multi-tier lifecycle:
  1. Student/Staff initiates request (`REQUESTED`).
  2. Finance Officer approves amount (`APPROVED`).
  3. Disbursement processed to bank/gateway (`PROCESSED`), which credits the student ledger and marks associated invoice lines accordingly.

