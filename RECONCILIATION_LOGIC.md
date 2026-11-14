# Financial Reconciliation Logic

The Reconciliation Engine (`ReconciliationService` in `backend/app/services/reconciliation_service.py`) automates periodic financial audits across the student ledger, invoice receivables, and payment allocations.

---

## 1. Multi-Stage Reconciliation Protocol

For each invoice in the audit scope (optionally filtered by academic term or degree program), the engine executes a 3-way balance verification:

```
[ Invoice Record ]                      [ Line Items ]                    [ Allocations & Ledger ]
Gross Amount = G        <==== MATCH? ====> Sum(Lines.Gross) = G_lines
Net Amount = N          <==== MATCH? ====> Gross - Scholarship Discount
Amount Paid = P         <==== MATCH? ====> Sum(PaymentAllocations) = P_alloc
Outstanding = B         <==== MATCH? ====> Net Amount - Amount Paid = B_calc
```

### 1.1 Balance Invariant Checks
1. **Invoice Line Sum Integrity**:
   $$\text{Invoice.gross\_amount} == \sum \text{InvoiceLine.gross\_amount}$$
2. **Net Collectible Invariant**:
   $$\text{Invoice.net\_amount} == \max(0.00, \text{Invoice.gross\_amount} - \text{Invoice.scholarship\_discount})$$
3. **Allocation Settlement Invariant**:
   $$\text{Invoice.amount\_paid} == \sum_{\text{alloc} \in \text{lines}} \text{PaymentAllocation.amount}$$
4. **Outstanding Balance Invariant**:
   $$\text{Invoice.outstanding\_balance} == \max(0.00, \text{Invoice.net\_amount} - \text{Invoice.amount\_paid})$$

---

## 2. Classification of Audit Results

Each evaluated record is classified into one of three statuses in `reconciliation_results`:

1. **`MATCHED`**:
   - $\Delta = |\text{Expected Amount} - \text{Actual Amount}| = 0.00$.
   - All 4 balance invariants hold strictly.
2. **`MISMATCHED`**:
   - $\Delta > 0.00$.
   - Financial variance detected between invoice header and allocated payment receipts or line items.
3. **`EXCEPTION`**:
   - Orphaned invoice without lines, negative balance, or unexpected status inconsistency.
   - Categorized by `exception_type` (e.g. `LINE_SUM_MISMATCH`, `ALLOCATION_MISMATCH`, `NEGATIVE_BALANCE`).

---

## 3. Reconciliation Execution & API Workflow

1. **Trigger Audit**: `POST /api/v1/reconciliation/run`
   - Creates a new `ReconciliationRun` record with status `IN_PROGRESS`.
   - Iterates through target invoice population within a database transaction.
   - Populates line-by-line findings into `reconciliation_results`.
   - Updates run summary totals (`matched_count`, `mismatched_count`, `exception_count`).
   - Marks run as `COMPLETED`.
2. **Audit Inspection**: `GET /api/v1/reconciliation/runs` and `GET /api/v1/reconciliation/runs/{id}/results`
   - Finance officers review variances, variance amounts, and associated exception notes directly in the frontend UI.
