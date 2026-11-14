import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { invoicesApi } from '../api/invoices';
import StatusBadge from '../components/common/StatusBadge';
import Modal from '../components/common/Modal';
import {
  ArrowLeft,
  FileText,
  User,
  Calendar,
  DollarSign,
  AlertCircle,
  XCircle,
  CheckCircle,
  Clock,
  Layers,
} from 'lucide-react';

export default function InvoiceDetails() {
  const { id } = useParams();
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Cancel Modal State
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState(null);

  const fetchInvoice = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await invoicesApi.getInvoice(id);
      setInvoice(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load invoice details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoice();
  }, [id]);

  const handleCancelInvoice = async (e) => {
    e.preventDefault();
    setCancelling(true);
    setCancelError(null);
    try {
      await invoicesApi.cancelInvoice(invoice.id, cancelReason);
      setIsCancelModalOpen(false);
      setCancelReason('');
      fetchInvoice();
    } catch (err) {
      setCancelError(err.response?.data?.detail || 'Failed to cancel invoice');
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-slate-500">Loading invoice details...</div>;
  }

  if (error || !invoice) {
    return (
      <div className="p-8 text-center text-rose-600 bg-white rounded-xl border border-rose-200">
        <AlertCircle className="w-8 h-8 mx-auto mb-2" />
        <p className="font-semibold">{error || 'Invoice not found'}</p>
        <Link to="/invoices" className="mt-4 inline-block btn-secondary text-xs">
          &larr; Back to Invoices
        </Link>
      </div>
    );
  }

  const canCancel = invoice.status !== 'CANCELLED' && invoice.status !== 'PAID';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          to="/invoices"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Invoices
        </Link>

        {canCancel && (
          <button
            onClick={() => setIsCancelModalOpen(true)}
            className="btn-secondary text-xs text-rose-600 hover:text-rose-700 flex items-center gap-1.5"
          >
            <XCircle className="w-3.5 h-3.5" />
            Cancel Invoice
          </button>
        )}
      </div>

      {/* Invoice Overview Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-slate-100 gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-primary-50 border border-primary-100 rounded-xl flex items-center justify-center text-primary-600 font-bold text-xl shadow-xs">
              <FileText className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-slate-900">{invoice.invoice_id}</h1>
                <StatusBadge status={invoice.status} />
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Billing Cycle: <span className="font-semibold text-slate-700">{invoice.billing_cycle}</span> | Term:{' '}
                <span className="font-medium text-slate-700">{invoice.term?.name || `Term #${invoice.term_id}`}</span>
              </p>
            </div>
          </div>
        </div>

        {/* Student & Dates Information Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-6">
          <div className="flex items-start gap-3">
            <User className="w-5 h-5 text-slate-400 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-slate-400">Student</p>
              <Link
                to={`/students/${invoice.student_id}`}
                className="text-sm font-bold text-primary-600 hover:underline mt-0.5 block"
              >
                {invoice.student?.first_name} {invoice.student?.last_name}
              </Link>
              <p className="text-xs text-slate-500 font-mono">ID: {invoice.student?.student_id}</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Calendar className="w-5 h-5 text-slate-400 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-slate-400">Issue Date</p>
              <p className="text-sm font-semibold text-slate-800 mt-0.5">{invoice.invoice_date}</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Clock className="w-5 h-5 text-slate-400 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-slate-400">Due Date</p>
              <p className="text-sm font-semibold text-slate-800 mt-0.5">{invoice.due_date}</p>
            </div>
          </div>
        </div>

        {invoice.notes && (
          <div className="mt-6 pt-6 border-t border-slate-100">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Invoice Notes</h2>
            <p className="text-xs text-slate-600">{invoice.notes}</p>
          </div>
        )}
      </div>

      {/* Financial Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <p className="text-xs font-medium text-slate-400">Gross Amount</p>
          <p className="text-lg font-bold text-slate-900 mt-1">
            INR {parseFloat(invoice.gross_amount || 0).toLocaleString()}
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <p className="text-xs font-medium text-slate-400">Scholarship Discount</p>
          <p className="text-lg font-bold text-emerald-600 mt-1">
            -INR {parseFloat(invoice.scholarship_discount || 0).toLocaleString()}
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <p className="text-xs font-medium text-slate-400">Net Due</p>
          <p className="text-lg font-bold text-slate-900 mt-1">
            INR {parseFloat(invoice.net_amount || 0).toLocaleString()}
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <p className="text-xs font-medium text-slate-400">Amount Paid</p>
          <p className="text-lg font-bold text-blue-600 mt-1">
            INR {parseFloat(invoice.amount_paid || 0).toLocaleString()}
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-rose-200 bg-rose-50/20 shadow-xs">
          <p className="text-xs font-medium text-rose-500">Outstanding Balance</p>
          <p className="text-lg font-bold text-rose-600 mt-1">
            INR {parseFloat(invoice.outstanding_balance || 0).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Line Items Breakdown Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-primary-600" />
            <h2 className="text-sm font-semibold text-slate-900">Line Items Breakdown</h2>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            {invoice.lines?.length || 0} Charge Items
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3">Line ID</th>
                <th className="px-6 py-3">Fee Type</th>
                <th className="px-6 py-3">Description</th>
                <th className="px-6 py-3">Amount</th>
                <th className="px-6 py-3">Allocated Paid</th>
                <th className="px-6 py-3">Remaining</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-700">
              {invoice.lines?.map((line) => (
                <tr key={line.id} className="hover:bg-slate-50/50">
                  <td className="px-6 py-3.5 font-mono font-medium text-slate-900">{line.invoice_line_id}</td>
                  <td className="px-6 py-3.5 font-semibold text-slate-800">{line.fee_type}</td>
                  <td className="px-6 py-3.5 text-slate-600">{line.description}</td>
                  <td className="px-6 py-3.5 font-medium">INR {parseFloat(line.amount || 0).toLocaleString()}</td>
                  <td className="px-6 py-3.5 text-blue-600 font-medium">
                    INR {parseFloat(line.allocated_amount || 0).toLocaleString()}
                  </td>
                  <td className="px-6 py-3.5 font-bold text-slate-900">
                    INR {parseFloat(line.remaining_amount || 0).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cancel Invoice Modal */}
      <Modal isOpen={isCancelModalOpen} onClose={() => setIsCancelModalOpen(false)} title="Cancel Tuition Invoice">
        <form onSubmit={handleCancelInvoice} className="space-y-4">
          {cancelError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{cancelError}</span>
            </div>
          )}

          <p className="text-xs text-rose-700 bg-rose-50 p-3 rounded-lg border border-rose-200">
            Cancelling this invoice will nullify all unpaid balances and charge lines. This action is auditable and final.
          </p>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Reason for Cancellation</label>
            <textarea
              required
              rows={3}
              className="input-field"
              placeholder="State reason for invoice cancellation..."
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsCancelModalOpen(false)}
              className="btn-secondary text-xs"
              disabled={cancelling}
            >
              Abort
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-rose-600 text-white rounded-lg text-xs font-medium hover:bg-rose-700"
              disabled={cancelling}
            >
              {cancelling ? 'Cancelling...' : 'Confirm Cancellation'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
