import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { invoicesApi } from '../api/invoices';
import { enrollmentsApi } from '../api/enrollments';
import StatusBadge from '../components/common/StatusBadge';
import Pagination from '../components/common/Pagination';
import Modal from '../components/common/Modal';
import { Receipt, Plus, Eye, AlertCircle } from 'lucide-react';

export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Enrollments for generate modal
  const [enrollmentsList, setEnrollmentsList] = useState([]);

  // Generate Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [formData, setFormData] = useState({
    enrollment_id: '',
    notes: '',
  });

  const fetchInvoices = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await invoicesApi.getInvoices({
        page,
        page_size: 15,
        status: statusFilter || undefined,
      });
      setInvoices(data.items);
      setTotal(data.total);
      setPages(data.pages);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    enrollmentsApi.getEnrollments({ status: 'ACTIVE', page_size: 100 })
      .then((d) => setEnrollmentsList(d.items || []))
      .catch((e) => console.error(e));
  }, []);

  useEffect(() => {
    fetchInvoices();
  }, [page, statusFilter]);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      await invoicesApi.generateInvoice({
        enrollment_id: parseInt(formData.enrollment_id, 10),
        notes: formData.notes,
      });
      setIsModalOpen(false);
      setFormData({ enrollment_id: '', notes: '' });
      fetchInvoices();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to generate tuition invoice');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Tuition Invoices</h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated billing engine, line-item charge composition, and receivable ledgers.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Generate Invoice
        </button>
      </div>

      {/* Filter */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
        <label className="text-xs font-semibold text-slate-600 uppercase">Status:</label>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="border border-slate-300 rounded-lg text-sm px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Statuses</option>
          <option value="ISSUED">Issued</option>
          <option value="PARTIALLY_PAID">Partially Paid</option>
          <option value="PAID">Paid</option>
          <option value="OVERDUE">Overdue</option>
          <option value="CANCELLED">Cancelled</option>
          <option value="REFUNDED">Refunded</option>
        </select>
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">Loading invoices...</div>
        ) : error ? (
          <div className="p-8 text-center text-rose-600 flex items-center justify-center gap-2">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        ) : invoices.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            No invoices generated yet. Click "Generate Invoice" above to issue tuition bills.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Invoice ID</th>
                  <th className="px-6 py-3.5">Student</th>
                  <th className="px-6 py-3.5">Cycle</th>
                  <th className="px-6 py-3.5">Due Date</th>
                  <th className="px-6 py-3.5">Gross Amount</th>
                  <th className="px-6 py-3.5">Net Payable</th>
                  <th className="px-6 py-3.5 font-bold text-slate-900">Outstanding</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-slate-900">
                      {inv.invoice_id}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-slate-900">
                        {inv.student?.first_name} {inv.student?.last_name}
                      </span>
                      <p className="text-xs text-slate-500 font-mono">{inv.student?.student_id}</p>
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-800">{inv.billing_cycle}</td>
                    <td className="px-6 py-4 text-xs text-slate-500">{inv.due_date}</td>
                    <td className="px-6 py-4 font-mono text-slate-700">
                      ₹{parseFloat(inv.gross_amount).toLocaleString('en-IN')}
                    </td>
                    <td className="px-6 py-4 font-mono font-semibold text-slate-900">
                      ₹{parseFloat(inv.net_amount).toLocaleString('en-IN')}
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-primary-700">
                      ₹{parseFloat(inv.outstanding_balance).toLocaleString('en-IN')}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={inv.status} />
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/invoices/${inv.id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-primary-600 hover:text-primary-700"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Lines
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <Pagination
          page={page}
          pages={pages}
          total={total}
          onPageChange={(p) => setPage(p)}
        />
      </div>

      {/* Generate Invoice Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Generate Tuition Invoice"
      >
        {formError && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{formError}</span>
          </div>
        )}

        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Select Active Enrollment *
            </label>
            <select
              required
              value={formData.enrollment_id}
              onChange={(e) => setFormData({ ...formData, enrollment_id: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
            >
              <option value="">Choose Student Enrollment</option>
              {enrollmentsList.map((enr) => (
                <option key={enr.id} value={enr.id}>
                  {enr.enrollment_id}: {enr.student?.first_name} {enr.student?.last_name} ({enr.program?.code} - {enr.term?.term_id})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Billing Cycle Notes
            </label>
            <textarea
              rows={2}
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              placeholder="e.g. Regular semester billing"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary text-xs"
            >
              {submitting ? 'Generating...' : 'Issue Invoice'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

