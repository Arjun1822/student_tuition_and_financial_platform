import React, { useState, useEffect } from 'react';
import { paymentsApi } from '../api/payments';
import StatusBadge from '../components/common/StatusBadge';
import Pagination from '../components/common/Pagination';
import Modal from '../components/common/Modal';
import { CreditCard, Plus, RotateCcw, ListFilter, Eye, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Payments() {
  const [payments, setPayments] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [methodFilter, setMethodFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Record Payment Modal
  const [isRecordModalOpen, setIsRecordModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [recordError, setRecordError] = useState(null);
  const [formData, setFormData] = useState({
    student_id: '',
    amount: '',
    payment_method: 'BANK_TRANSFER',
    reference_number: '',
    notes: '',
    auto_allocate: true,
    invoice_id: '',
  });

  // Reversal Modal
  const [reversalPayment, setReversalPayment] = useState(null);
  const [reversalReason, setReversalReason] = useState('');
  const [reversalSubmitting, setReversalSubmitting] = useState(false);
  const [reversalError, setReversalError] = useState(null);

  // Allocations Modal
  const [viewAllocationsPayment, setViewAllocationsPayment] = useState(null);
  const [allocations, setAllocations] = useState([]);
  const [allocationsLoading, setAllocationsLoading] = useState(false);

  const fetchPayments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await paymentsApi.getPayments({
        page,
        page_size: 15,
        status: statusFilter || undefined,
        payment_method: methodFilter || undefined,
      });
      setPayments(data.items || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load payments history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();
  }, [page, statusFilter, methodFilter]);

  const handleRecordPayment = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setRecordError(null);
    try {
      await paymentsApi.recordPayment({
        student_id: parseInt(formData.student_id, 10),
        amount: parseFloat(formData.amount),
        payment_method: formData.payment_method,
        reference_number: formData.reference_number || undefined,
        notes: formData.notes || undefined,
        auto_allocate: Boolean(formData.auto_allocate),
        invoice_id: formData.invoice_id ? parseInt(formData.invoice_id, 10) : undefined,
      });
      setIsRecordModalOpen(false);
      setFormData({
        student_id: '',
        amount: '',
        payment_method: 'BANK_TRANSFER',
        reference_number: '',
        notes: '',
        auto_allocate: true,
        invoice_id: '',
      });
      setActionSuccess('Payment recorded and allocated successfully.');
      fetchPayments();
    } catch (err) {
      setRecordError(err.response?.data?.detail || 'Failed to record payment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReversePayment = async () => {
    if (!reversalPayment) return;
    if (!reversalReason || reversalReason.length < 3) {
      setReversalError('Reversal reason is required (min 3 characters).');
      return;
    }
    setReversalSubmitting(true);
    setReversalError(null);
    try {
      await paymentsApi.reversePayment(reversalPayment.id, {
        reason: reversalReason,
      });
      setReversalPayment(null);
      setReversalReason('');
      setActionSuccess(`Payment ${reversalPayment.payment_id} reversed successfully.`);
      fetchPayments();
    } catch (err) {
      setReversalError(err.response?.data?.detail || 'Reversal failed');
    } finally {
      setReversalSubmitting(false);
    }
  };

  const handleViewAllocations = async (payment) => {
    setViewAllocationsPayment(payment);
    setAllocationsLoading(true);
    try {
      const data = await paymentsApi.getPaymentAllocations({ payment_id: payment.id });
      setAllocations(data.items || (Array.isArray(data) ? data : []));
    } catch (err) {
      console.error(err);
      setAllocations([]);
    } finally {
      setAllocationsLoading(false);
    }
  };

  const formatCurrency = (val) => {
    const num = parseFloat(val) || 0;
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Payments & Receipts</h1>
          <p className="text-sm text-slate-500 mt-1">
            Omni-channel payment collection, line-item ledger allocation, and transactional reversals.
          </p>
        </div>
        <button
          onClick={() => setIsRecordModalOpen(true)}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Record Payment
        </button>
      </div>

      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm flex items-center justify-between">
          <span>{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-600 font-bold hover:underline">Dismiss</button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-600 font-bold hover:underline">Dismiss</button>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center gap-3">
          <label className="text-xs font-semibold text-slate-600 uppercase">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="input-field text-sm py-1.5 px-3 w-36"
          >
            <option value="">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="REVERSED">Reversed</option>
            <option value="REFUNDED">Refunded</option>
            <option value="FAILED">Failed</option>
            <option value="PENDING">Pending</option>
          </select>

          <label className="text-xs font-semibold text-slate-600 uppercase ml-2">Method:</label>
          <select
            value={methodFilter}
            onChange={(e) => { setMethodFilter(e.target.value); setPage(1); }}
            className="input-field text-sm py-1.5 px-3 w-40"
          >
            <option value="">All Methods</option>
            <option value="BANK_TRANSFER">Bank Transfer</option>
            <option value="CREDIT_CARD">Credit Card</option>
            <option value="DEBIT_CARD">Debit Card</option>
            <option value="UPI">UPI</option>
            <option value="NET_BANKING">Net Banking</option>
            <option value="CHEQUE">Cheque</option>
            <option value="CASH">Cash</option>
          </select>
        </div>
        <span className="text-xs text-slate-500 font-medium">{total} total payment transactions</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Payment ID</th>
                <th className="px-6 py-3.5">Student</th>
                <th className="px-6 py-3.5">Method & Ref</th>
                <th className="px-6 py-3.5">Amount</th>
                <th className="px-6 py-3.5">Allocated</th>
                <th className="px-6 py-3.5">Unallocated</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-normal text-slate-800">
              {loading ? (
                <tr><td colSpan="8" className="px-6 py-12 text-center text-slate-400">Loading payments...</td></tr>
              ) : payments.length === 0 ? (
                <tr><td colSpan="8" className="px-6 py-12 text-center text-slate-400">No payment records found.</td></tr>
              ) : (
                payments.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs font-semibold text-primary-700">{p.payment_id}</td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-slate-900">{p.student_name || `Student #${p.student_id}`}</p>
                      <p className="font-mono text-xs text-slate-400">{p.student_business_id}</p>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-700 font-medium">{p.payment_method}</span>
                      {p.reference_number && (
                        <p className="font-mono text-[11px] text-slate-400 mt-0.5">{p.reference_number}</p>
                      )}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs font-bold text-slate-900">{formatCurrency(p.amount)}</td>
                    <td className="px-6 py-4 font-mono text-xs text-emerald-700">{formatCurrency(p.allocated_amount)}</td>
                    <td className="px-6 py-4 font-mono text-xs text-amber-700">{formatCurrency(p.unallocated_amount)}</td>
                    <td className="px-6 py-4"><StatusBadge status={p.status} /></td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleViewAllocations(p)}
                          className="px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 border border-slate-200 rounded hover:bg-slate-50 flex items-center gap-1"
                        >
                          <Eye className="w-3.5 h-3.5" /> Allocations
                        </button>
                        {p.status === 'COMPLETED' && (
                          <button
                            onClick={() => { setReversalPayment(p); setReversalReason(''); setReversalError(null); }}
                            className="px-2.5 py-1 text-xs font-medium text-rose-600 hover:text-rose-700 border border-rose-200 rounded hover:bg-rose-50 flex items-center gap-1"
                          >
                            <RotateCcw className="w-3.5 h-3.5" /> Reverse
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="p-4 border-t border-slate-200">
          <Pagination currentPage={page} totalPages={pages} onPageChange={setPage} />
        </div>
      </div>

      {/* RECORD PAYMENT MODAL */}
      <Modal
        isOpen={isRecordModalOpen}
        onClose={() => setIsRecordModalOpen(false)}
        title="Record Student Payment"
      >
        <form onSubmit={handleRecordPayment} className="space-y-4">
          {recordError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
              {recordError}
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Student Primary Database ID *</label>
            <input
              type="number"
              required
              value={formData.student_id}
              onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
              className="input-field w-full text-sm"
              placeholder="e.g. 1"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Payment Amount (₹) *</label>
            <input
              type="number"
              step="0.01"
              min="1"
              required
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              className="input-field w-full text-sm"
              placeholder="50000.00"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Payment Method *</label>
              <select
                value={formData.payment_method}
                onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                className="input-field w-full text-sm"
              >
                <option value="BANK_TRANSFER">Bank Transfer</option>
                <option value="CREDIT_CARD">Credit Card</option>
                <option value="DEBIT_CARD">Debit Card</option>
                <option value="UPI">UPI</option>
                <option value="NET_BANKING">Net Banking</option>
                <option value="CHEQUE">Cheque</option>
                <option value="CASH">Cash</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Reference / UTR #</label>
              <input
                type="text"
                value={formData.reference_number}
                onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
                className="input-field w-full text-sm"
                placeholder="UTR-2026-XXXX"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Target Invoice ID (Optional)</label>
            <input
              type="number"
              value={formData.invoice_id}
              onChange={(e) => setFormData({ ...formData, invoice_id: e.target.value })}
              className="input-field w-full text-sm"
              placeholder="Leave blank for automatic oldest-first allocation"
            />
          </div>
          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="auto_allocate"
              checked={formData.auto_allocate}
              onChange={(e) => setFormData({ ...formData, auto_allocate: e.target.checked })}
              className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="auto_allocate" className="text-xs text-slate-700">
              Automatically allocate to outstanding invoice lines in statutory order (Tuition, Lab, Exam)
            </label>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Notes</label>
            <textarea
              rows="2"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="input-field w-full text-sm"
              placeholder="Optional remarks..."
            />
          </div>
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsRecordModalOpen(false)}
              className="btn-secondary text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary text-sm"
            >
              {submitting ? 'Recording Payment...' : 'Record Payment'}
            </button>
          </div>
        </form>
      </Modal>

      {/* REVERSAL MODAL */}
      <Modal
        isOpen={!!reversalPayment}
        onClose={() => setReversalPayment(null)}
        title="Reverse Payment Transaction"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            Reversing payment <span className="font-semibold text-slate-900">{reversalPayment?.payment_id}</span> ({formatCurrency(reversalPayment?.amount)}) will restore invoice line balances and record an immutable ledger reversal event.
          </p>
          {reversalError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
              {reversalError}
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Reversal Reason *</label>
            <textarea
              rows="3"
              required
              value={reversalReason}
              onChange={(e) => setReversalReason(e.target.value)}
              className="input-field w-full text-sm"
              placeholder="e.g. Chargeback, cheque bounce, or administrative correction"
            />
          </div>
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setReversalPayment(null)}
              className="btn-secondary text-sm"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={reversalSubmitting}
              onClick={handleReversePayment}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-sm font-semibold"
            >
              {reversalSubmitting ? 'Reversing...' : 'Confirm Reversal'}
            </button>
          </div>
        </div>
      </Modal>

      {/* VIEW ALLOCATIONS MODAL */}
      <Modal
        isOpen={!!viewAllocationsPayment}
        onClose={() => setViewAllocationsPayment(null)}
        title={`Payment Allocations — ${viewAllocationsPayment?.payment_id}`}
      >
        <div className="space-y-4">
          <div className="flex justify-between items-center bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
            <div>
              <span className="text-slate-500">Total Collected:</span>{' '}
              <span className="font-bold text-slate-900">{formatCurrency(viewAllocationsPayment?.amount)}</span>
            </div>
            <div>
              <span className="text-slate-500">Allocated:</span>{' '}
              <span className="font-bold text-emerald-700">{formatCurrency(viewAllocationsPayment?.allocated_amount)}</span>
            </div>
            <div>
              <span className="text-slate-500">Unallocated:</span>{' '}
              <span className="font-bold text-amber-700">{formatCurrency(viewAllocationsPayment?.unallocated_amount)}</span>
            </div>
          </div>

          {allocationsLoading ? (
            <p className="text-center py-6 text-slate-400 text-sm">Loading allocations...</p>
          ) : allocations.length === 0 ? (
            <p className="text-center py-6 text-slate-400 text-sm">No line-item allocations found for this payment.</p>
          ) : (
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-semibold uppercase">
                  <tr>
                    <th className="px-4 py-2.5">Allocation ID</th>
                    <th className="px-4 py-2.5">Invoice Line</th>
                    <th className="px-4 py-2.5">Allocated Amount</th>
                    <th className="px-4 py-2.5">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-800">
                  {allocations.map((a) => (
                    <tr key={a.id}>
                      <td className="px-4 py-2.5 font-mono text-primary-700">{a.allocation_id || `#${a.id}`}</td>
                      <td className="px-4 py-2.5 font-mono">Line #{a.invoice_line_id}</td>
                      <td className="px-4 py-2.5 font-mono font-bold text-emerald-700">{formatCurrency(a.amount)}</td>
                      <td className="px-4 py-2.5 text-slate-500">
                        {a.allocated_at ? new Date(a.allocated_at).toLocaleDateString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex justify-end pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setViewAllocationsPayment(null)}
              className="btn-secondary text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
