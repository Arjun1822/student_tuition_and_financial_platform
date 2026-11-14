import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { enrollmentsApi } from '../api/enrollments';
import { invoicesApi } from '../api/invoices';
import StatusBadge from '../components/common/StatusBadge';
import Modal from '../components/common/Modal';
import {
  ArrowLeft,
  UserCheck,
  BookOpen,
  Calendar,
  FileText,
  PlusCircle,
  XCircle,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

export default function EnrollmentDetails() {
  const { id } = useParams();
  const [enrollment, setEnrollment] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Generate Invoice Modal
  const [isInvoiceModalOpen, setIsInvoiceModalOpen] = useState(false);
  const [invoiceDueDate, setInvoiceDueDate] = useState('');
  const [invoiceNotes, setInvoiceNotes] = useState('');
  const [generatingInvoice, setGeneratingInvoice] = useState(false);
  const [invoiceError, setInvoiceError] = useState(null);

  // Cancel Modal
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState(null);

  // Withdraw Modal
  const [isWithdrawModalOpen, setIsWithdrawModalOpen] = useState(false);
  const [withdrawReason, setWithdrawReason] = useState('');
  const [withdrawing, setWithdrawing] = useState(false);
  const [withdrawError, setWithdrawError] = useState(null);

  const fetchEnrollmentData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await enrollmentsApi.getEnrollment(id);
      setEnrollment(data);

      // Fetch related invoices
      try {
        const invData = await invoicesApi.getInvoices({ enrollment_id: data.id });
        setInvoices(invData.items || []);
      } catch (iErr) {
        setInvoices([]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load enrollment record');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnrollmentData();
  }, [id]);

  const handleGenerateInvoice = async (e) => {
    e.preventDefault();
    setGeneratingInvoice(true);
    setInvoiceError(null);
    try {
      await invoicesApi.generateInvoice({
        enrollment_id: enrollment.id,
        due_date: invoiceDueDate || undefined,
        notes: invoiceNotes || undefined,
      });
      setIsInvoiceModalOpen(false);
      setInvoiceDueDate('');
      setInvoiceNotes('');
      fetchEnrollmentData();
    } catch (err) {
      setInvoiceError(err.response?.data?.detail || 'Failed to generate tuition invoice');
    } finally {
      setGeneratingInvoice(false);
    }
  };

  const handleCancelEnrollment = async (e) => {
    e.preventDefault();
    setCancelling(true);
    setCancelError(null);
    try {
      await enrollmentsApi.cancelEnrollment(enrollment.id, cancelReason);
      setIsCancelModalOpen(false);
      setCancelReason('');
      fetchEnrollmentData();
    } catch (err) {
      setCancelError(err.response?.data?.detail || 'Failed to cancel enrollment');
    } finally {
      setCancelling(false);
    }
  };

  const handleWithdrawEnrollment = async (e) => {
    e.preventDefault();
    setWithdrawing(true);
    setWithdrawError(null);
    try {
      await enrollmentsApi.withdrawEnrollment(enrollment.id, withdrawReason);
      setIsWithdrawModalOpen(false);
      setWithdrawReason('');
      fetchEnrollmentData();
    } catch (err) {
      setWithdrawError(err.response?.data?.detail || 'Failed to process withdrawal');
    } finally {
      setWithdrawing(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-slate-500">Loading enrollment record...</div>;
  }

  if (error || !enrollment) {
    return (
      <div className="p-8 text-center text-rose-600 bg-white rounded-xl border border-rose-200">
        <AlertCircle className="w-8 h-8 mx-auto mb-2" />
        <p className="font-semibold">{error || 'Enrollment record not found'}</p>
        <Link to="/enrollments" className="mt-4 inline-block btn-secondary text-xs">
          &larr; Back to Enrollments
        </Link>
      </div>
    );
  }

  const isActive = enrollment.status === 'ACTIVE';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          to="/enrollments"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Enrollments
        </Link>

        {isActive && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsInvoiceModalOpen(true)}
              className="btn-primary flex items-center gap-1.5 text-xs"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              Generate Invoice
            </button>
            <button
              onClick={() => setIsWithdrawModalOpen(true)}
              className="btn-secondary flex items-center gap-1.5 text-xs text-amber-700 hover:text-amber-800"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              Withdraw
            </button>
            <button
              onClick={() => setIsCancelModalOpen(true)}
              className="btn-secondary flex items-center gap-1.5 text-xs text-rose-600 hover:text-rose-700"
            >
              <XCircle className="w-3.5 h-3.5" />
              Cancel Enrollment
            </button>
          </div>
        )}
      </div>

      {/* Main Enrollment Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-slate-100 gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-blue-50 border border-blue-100 rounded-xl flex items-center justify-center text-blue-600 font-bold text-xl shadow-xs">
              <UserCheck className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-slate-900">{enrollment.enrollment_id}</h1>
                <StatusBadge status={enrollment.status} />
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Enrolled on: <span className="font-medium text-slate-700">{enrollment.enrollment_date}</span>
              </p>
            </div>
          </div>
        </div>

        {/* Triple Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
          {/* Student Info */}
          <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 space-y-2">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Student Profile</p>
            <Link
              to={`/students/${enrollment.student_id}`}
              className="text-sm font-bold text-primary-600 hover:underline block"
            >
              {enrollment.student?.first_name} {enrollment.student?.last_name}
            </Link>
            <p className="text-xs text-slate-600 font-mono">ID: {enrollment.student?.student_id}</p>
            <p className="text-xs text-slate-500">{enrollment.student?.email}</p>
          </div>

          {/* Program Info */}
          <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 space-y-2">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Academic Program</p>
            <Link
              to={`/programs/${enrollment.program_id}`}
              className="text-sm font-bold text-primary-600 hover:underline block"
            >
              {enrollment.program?.name}
            </Link>
            <p className="text-xs text-slate-600 font-mono">Code: {enrollment.program?.code}</p>
            <p className="text-xs text-slate-500">{enrollment.program?.department}</p>
          </div>

          {/* Term Info */}
          <div className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 space-y-2">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Academic Term</p>
            <p className="text-sm font-bold text-slate-800">{enrollment.term?.name}</p>
            <p className="text-xs text-slate-600 font-mono">{enrollment.term?.term_id}</p>
            <p className="text-xs text-slate-500">Year: {enrollment.term?.year} | {enrollment.term?.semester}</p>
          </div>
        </div>

        {/* Cancellation or Withdrawal Notices */}
        {enrollment.cancellation_date && (
          <div className="mt-6 p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-xs">
            <p className="font-semibold">Cancelled on {enrollment.cancellation_date}</p>
            <p className="mt-1">Reason: {enrollment.cancellation_reason || 'No reason provided'}</p>
          </div>
        )}
        {enrollment.withdrawal_date && (
          <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-xs">
            <p className="font-semibold">Withdrawn on {enrollment.withdrawal_date}</p>
            <p className="mt-1">Reason: {enrollment.withdrawal_reason || 'No reason provided'}</p>
          </div>
        )}
      </div>

      {/* Generated Invoices Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-primary-600" />
            <h2 className="text-sm font-semibold text-slate-900">Billing Invoices</h2>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            {invoices.length} {invoices.length === 1 ? 'Invoice' : 'Invoices'}
          </span>
        </div>

        {invoices.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No invoices generated yet for this enrollment.
            {isActive && (
              <div className="mt-3">
                <button
                  onClick={() => setIsInvoiceModalOpen(true)}
                  className="btn-secondary text-xs inline-flex items-center gap-1.5"
                >
                  <PlusCircle className="w-3.5 h-3.5" /> Generate First Invoice
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Invoice ID</th>
                  <th className="px-6 py-3">Cycle</th>
                  <th className="px-6 py-3">Gross</th>
                  <th className="px-6 py-3">Discount</th>
                  <th className="px-6 py-3">Net Due</th>
                  <th className="px-6 py-3">Paid</th>
                  <th className="px-6 py-3">Balance</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-3.5 font-mono font-medium text-slate-900">{inv.invoice_id}</td>
                    <td className="px-6 py-3.5">{inv.billing_cycle}</td>
                    <td className="px-6 py-3.5">INR {parseFloat(inv.gross_amount || 0).toLocaleString()}</td>
                    <td className="px-6 py-3.5 text-emerald-600 font-medium">
                      -INR {parseFloat(inv.scholarship_discount || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-3.5 font-semibold text-slate-900">
                      INR {parseFloat(inv.net_amount || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-3.5 text-blue-600 font-medium">
                      INR {parseFloat(inv.amount_paid || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-3.5 font-bold text-rose-600">
                      INR {parseFloat(inv.outstanding_balance || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-3.5">
                      <StatusBadge status={inv.status} />
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <Link
                        to={`/invoices/${inv.id}`}
                        className="text-xs font-semibold text-primary-600 hover:underline"
                      >
                        View &rarr;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Generate Invoice Modal */}
      <Modal isOpen={isInvoiceModalOpen} onClose={() => setIsInvoiceModalOpen(false)} title="Generate Tuition Invoice">
        <form onSubmit={handleGenerateInvoice} className="space-y-4">
          {invoiceError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{invoiceError}</span>
            </div>
          )}

          <p className="text-xs text-slate-600">
            This operation will calculate tuition and mandatory program fees for{' '}
            <strong className="text-slate-800">{enrollment.enrollment_id}</strong> based on the term fee schedule.
          </p>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Due Date (Optional)</label>
            <input
              type="date"
              className="input-field"
              value={invoiceDueDate}
              onChange={(e) => setInvoiceDueDate(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Invoice Notes (Optional)</label>
            <textarea
              rows={2}
              className="input-field"
              placeholder="e.g. Standard fall semester billing cycle"
              value={invoiceNotes}
              onChange={(e) => setInvoiceNotes(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsInvoiceModalOpen(false)}
              className="btn-secondary text-xs"
              disabled={generatingInvoice}
            >
              Cancel
            </button>
            <button type="submit" className="btn-primary text-xs" disabled={generatingInvoice}>
              {generatingInvoice ? 'Generating...' : 'Confirm Invoice Generation'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Cancel Enrollment Modal */}
      <Modal isOpen={isCancelModalOpen} onClose={() => setIsCancelModalOpen(false)} title="Cancel Student Enrollment">
        <form onSubmit={handleCancelEnrollment} className="space-y-4">
          {cancelError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{cancelError}</span>
            </div>
          )}
          <p className="text-xs text-rose-700 bg-rose-50 p-3 rounded-lg border border-rose-200">
            Warning: Cancelling enrollment marks the student registration invalid. This cannot be undone.
          </p>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Cancellation Reason</label>
            <textarea
              required
              rows={3}
              className="input-field"
              placeholder="Provide reason for cancellation..."
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

      {/* Withdraw Enrollment Modal */}
      <Modal isOpen={isWithdrawModalOpen} onClose={() => setIsWithdrawModalOpen(false)} title="Process Term Withdrawal">
        <form onSubmit={handleWithdrawEnrollment} className="space-y-4">
          {withdrawError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{withdrawError}</span>
            </div>
          )}
          <p className="text-xs text-amber-800 bg-amber-50 p-3 rounded-lg border border-amber-200">
            Processing term withdrawal will initiate institutional policy evaluations and financial adjustments.
          </p>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Withdrawal Reason</label>
            <textarea
              required
              rows={3}
              className="input-field"
              placeholder="Provide reason for withdrawal..."
              value={withdrawReason}
              onChange={(e) => setWithdrawReason(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsWithdrawModalOpen(false)}
              className="btn-secondary text-xs"
              disabled={withdrawing}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-amber-600 text-white rounded-lg text-xs font-medium hover:bg-amber-700"
              disabled={withdrawing}
            >
              {withdrawing ? 'Processing...' : 'Confirm Withdrawal'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
