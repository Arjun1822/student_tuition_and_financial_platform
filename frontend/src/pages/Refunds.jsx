import React, { useState, useEffect } from 'react';
import { refundsApi } from '../api/refunds';
import StatusBadge from '../components/common/StatusBadge';
import Pagination from '../components/common/Pagination';
import Modal from '../components/common/Modal';
import { RotateCcw, Plus, CheckCircle, ArrowRightCircle, XCircle, AlertCircle } from 'lucide-react';

export default function Refunds() {
  const [refunds, setRefunds] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Request Refund Modal
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [requestError, setRequestError] = useState(null);
  const [formData, setFormData] = useState({
    payment_id: '',
    student_id: '',
    invoice_id: '',
    amount: '',
    reason: '',
    reference_number: '',
    notes: '',
  });

  // Action Modals (Approve, Process, Reject)
  const [actionItem, setActionItem] = useState(null);
  const [actionType, setActionType] = useState(null); // 'approve' | 'process' | 'reject'
  const [actionReason, setActionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchRefunds = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await refundsApi.getRefunds({
        page,
        page_size: 15,
        status: statusFilter || undefined,
      });
      setRefunds(data.items || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load refund requests');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRefunds();
  }, [page, statusFilter]);

  const handleRequestRefund = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setRequestError(null);
    try {
      await refundsApi.requestRefund({
        payment_id: parseInt(formData.payment_id, 10),
        student_id: parseInt(formData.student_id, 10),
        invoice_id: formData.invoice_id ? parseInt(formData.invoice_id, 10) : undefined,
        amount: parseFloat(formData.amount),
        reason: formData.reason,
        reference_number: formData.reference_number || undefined,
        notes: formData.notes || undefined,
      });
      setIsRequestModalOpen(false);
      setFormData({
        payment_id: '',
        student_id: '',
        invoice_id: '',
        amount: '',
        reason: '',
        reference_number: '',
        notes: '',
      });
      setActionSuccess('Refund requested successfully.');
      fetchRefunds();
    } catch (err) {
      setRequestError(err.response?.data?.detail || 'Failed to submit refund request');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async () => {
    if (!actionItem) return;
    setActionLoading(true);
    try {
      await refundsApi.approveRefund(actionItem.id, {
        notes: actionReason || 'Approved via financial portal',
      });
      setActionItem(null);
      setActionSuccess(`Refund ${actionItem.refund_id} approved.`);
      fetchRefunds();
    } catch (err) {
      setError(err.response?.data?.detail || 'Approval failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleProcess = async () => {
    if (!actionItem) return;
    setActionLoading(true);
    try {
      await refundsApi.processRefund(actionItem.id);
      setActionItem(null);
      setActionSuccess(`Refund ${actionItem.refund_id} disbursed and processed to ledger.`);
      fetchRefunds();
    } catch (err) {
      setError(err.response?.data?.detail || 'Processing failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!actionItem) return;
    if (!actionReason || actionReason.length < 3) {
      setError('Please provide a rejection reason (min 3 characters).');
      return;
    }
    setActionLoading(true);
    try {
      await refundsApi.rejectRefund(actionItem.id, {
        reason: actionReason,
      });
      setActionItem(null);
      setActionSuccess(`Refund ${actionItem.refund_id} rejected.`);
      fetchRefunds();
    } catch (err) {
      setError(err.response?.data?.detail || 'Rejection failed');
    } finally {
      setActionLoading(false);
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
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Student Refunds & Withdrawals</h1>
          <p className="text-sm text-slate-500 mt-1">
            Term withdrawal claims, credit balance disbursement, and multi-tier approval governance.
          </p>
        </div>
        <button
          onClick={() => setIsRequestModalOpen(true)}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Request Refund
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
            className="input-field text-sm py-1.5 px-3 w-40"
          >
            <option value="">All Statuses</option>
            <option value="REQUESTED">Requested / Pending</option>
            <option value="APPROVED">Approved</option>
            <option value="PROCESSED">Processed / Disbursed</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
        <span className="text-xs text-slate-500 font-medium">{total} total refund requests</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Refund ID</th>
                <th className="px-6 py-3.5">Student</th>
                <th className="px-6 py-3.5">Payment Ref</th>
                <th className="px-6 py-3.5">Refund Amount</th>
                <th className="px-6 py-3.5">Reason</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Workflow Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-normal text-slate-800">
              {loading ? (
                <tr><td colSpan="7" className="px-6 py-12 text-center text-slate-400">Loading refunds...</td></tr>
              ) : refunds.length === 0 ? (
                <tr><td colSpan="7" className="px-6 py-12 text-center text-slate-400">No refund requests found.</td></tr>
              ) : (
                refunds.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs font-semibold text-primary-700">{r.refund_id}</td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-slate-900">{r.student_name || `Student #${r.student_id}`}</p>
                      <p className="font-mono text-xs text-slate-400">{r.student_business_id}</p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-mono text-xs text-slate-700">{r.payment_business_id || `Payment #${r.payment_id}`}</p>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs font-bold text-rose-700">{formatCurrency(r.amount)}</td>
                    <td className="px-6 py-4 text-xs text-slate-600 max-w-xs truncate">{r.reason}</td>
                    <td className="px-6 py-4"><StatusBadge status={r.status} /></td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {r.status === 'REQUESTED' && (
                          <>
                            <button
                              onClick={() => { setActionItem(r); setActionType('approve'); setActionReason(''); }}
                              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold flex items-center gap-1"
                            >
                              <CheckCircle className="w-3.5 h-3.5" /> Approve
                            </button>
                            <button
                              onClick={() => { setActionItem(r); setActionType('reject'); setActionReason(''); }}
                              className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded text-xs font-semibold flex items-center gap-1"
                            >
                              <XCircle className="w-3.5 h-3.5" /> Reject
                            </button>
                          </>
                        )}
                        {r.status === 'APPROVED' && (
                          <button
                            onClick={() => { setActionItem(r); setActionType('process'); setActionReason(''); }}
                            className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold flex items-center gap-1"
                          >
                            <ArrowRightCircle className="w-3.5 h-3.5" /> Process Disbursement
                          </button>
                        )}
                        {r.status === 'PROCESSED' && (
                          <span className="text-xs text-emerald-600 font-medium">Disbursed</span>
                        )}
                        {r.status === 'REJECTED' && (
                          <span className="text-xs text-rose-500 font-medium">Rejected</span>
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

      {/* REQUEST REFUND MODAL */}
      <Modal
        isOpen={isRequestModalOpen}
        onClose={() => setIsRequestModalOpen(false)}
        title="Initiate Student Refund Claim"
      >
        <form onSubmit={handleRequestRefund} className="space-y-4">
          {requestError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
              {requestError}
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Student Primary ID *</label>
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
              <label className="block text-xs font-semibold text-slate-700 mb-1">Payment ID *</label>
              <input
                type="number"
                required
                value={formData.payment_id}
                onChange={(e) => setFormData({ ...formData, payment_id: e.target.value })}
                className="input-field w-full text-sm"
                placeholder="e.g. 1"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Refund Amount (₹) *</label>
              <input
                type="number"
                step="0.01"
                min="1"
                required
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className="input-field w-full text-sm"
                placeholder="15000.00"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Invoice ID (Optional)</label>
              <input
                type="number"
                value={formData.invoice_id}
                onChange={(e) => setFormData({ ...formData, invoice_id: e.target.value })}
                className="input-field w-full text-sm"
                placeholder="e.g. 1"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Refund Reason *</label>
            <textarea
              rows="2"
              required
              value={formData.reason}
              onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
              className="input-field w-full text-sm"
              placeholder="e.g. Term withdrawal within 100% refund window"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Disbursement Reference (Optional)</label>
            <input
              type="text"
              value={formData.reference_number}
              onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
              className="input-field w-full text-sm"
              placeholder="REF-DISB-2026-XXXX"
            />
          </div>
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsRequestModalOpen(false)}
              className="btn-secondary text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary text-sm"
            >
              {submitting ? 'Submitting...' : 'Submit Refund Request'}
            </button>
          </div>
        </form>
      </Modal>

      {/* ACTION MODAL (APPROVE / PROCESS / REJECT) */}
      <Modal
        isOpen={!!actionItem}
        onClose={() => setActionItem(null)}
        title={
          actionType === 'approve'
            ? 'Approve Refund Claim'
            : actionType === 'process'
            ? 'Disburse & Process Refund'
            : 'Reject Refund Request'
        }
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            {actionType === 'approve' && `Authorize refund ${actionItem?.refund_id} for ${formatCurrency(actionItem?.amount)}.`}
            {actionType === 'process' && `Execute disbursement for refund ${actionItem?.refund_id} (${formatCurrency(actionItem?.amount)}). This will credit student ledger and update invoice paid balance.`}
            {actionType === 'reject' && `Reject refund request ${actionItem?.refund_id}.`}
          </p>
          {actionType !== 'process' && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {actionType === 'approve' ? 'Approval Notes' : 'Rejection Reason *'}
              </label>
              <textarea
                rows="3"
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                className="input-field w-full text-sm"
                placeholder={actionType === 'approve' ? 'Optional audit comments...' : 'Enter rejection justification...'}
              />
            </div>
          )}
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setActionItem(null)}
              className="btn-secondary text-sm"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={actionLoading}
              onClick={
                actionType === 'approve'
                  ? handleApprove
                  : actionType === 'process'
                  ? handleProcess
                  : handleReject
              }
              className={
                actionType === 'reject'
                  ? 'px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-sm font-semibold'
                  : 'btn-primary text-sm'
              }
            >
              {actionLoading ? 'Processing...' : 'Confirm'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

