import React, { useState, useEffect } from 'react';
import { ledgerApi } from '../api/ledger';
import Pagination from '../components/common/Pagination';
import Modal from '../components/common/Modal';
import { BookOpen, User, Search, Clock, DollarSign, AlertCircle, FileText, ArrowDownRight, ArrowUpRight } from 'lucide-react';

export default function Ledger() {
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Student Statement Modal
  const [isStatementModalOpen, setIsStatementModalOpen] = useState(false);
  const [searchStudentId, setSearchStudentId] = useState('');
  const [statement, setStatement] = useState(null);
  const [statementLoading, setStatementLoading] = useState(false);
  const [statementError, setStatementError] = useState(null);

  // Event Details Modal
  const [selectedEvent, setSelectedEvent] = useState(null);

  const fetchEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ledgerApi.getFinancialEvents({
        page,
        page_size: 20,
        event_type: eventTypeFilter || undefined,
        entity_type: entityTypeFilter || undefined,
      });
      setEvents(data.items || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load ledger events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [page, eventTypeFilter, entityTypeFilter]);

  const handleFetchStatement = async (e) => {
    e.preventDefault();
    if (!searchStudentId) return;
    setStatementLoading(true);
    setStatementError(null);
    setStatement(null);
    try {
      const data = await ledgerApi.getStudentStatement(parseInt(searchStudentId, 10));
      setStatement(data);
    } catch (err) {
      setStatementError(err.response?.data?.detail || 'Student not found or statement calculation failed');
    } finally {
      setStatementLoading(false);
    }
  };

  const formatCurrency = (val) => {
    const num = parseFloat(val) || 0;
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const isDebit = (type) => {
    return ['INVOICE_GENERATED', 'LATE_FEE_ASSESSED', 'PAYMENT_REVERSED'].includes(type);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Financial Ledger & Audit Log</h1>
          <p className="text-sm text-slate-500 mt-1">
            Immutable, append-only double-entry financial event ledger and real-time student statements.
          </p>
        </div>
        <button
          onClick={() => { setIsStatementModalOpen(true); setStatement(null); setStatementError(null); }}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto"
        >
          <User className="w-4 h-4" />
          Student Balance Statement
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-600 font-bold hover:underline">Dismiss</button>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center gap-3">
          <label className="text-xs font-semibold text-slate-600 uppercase">Event Type:</label>
          <select
            value={eventTypeFilter}
            onChange={(e) => { setEventTypeFilter(e.target.value); setPage(1); }}
            className="input-field text-sm py-1.5 px-3 w-52"
          >
            <option value="">All Event Types</option>
            <option value="INVOICE_GENERATED">Invoice Generated</option>
            <option value="PAYMENT_RECORDED">Payment Recorded</option>
            <option value="PAYMENT_ALLOCATED">Payment Allocated</option>
            <option value="PAYMENT_REVERSED">Payment Reversed</option>
            <option value="SCHOLARSHIP_APPLIED">Scholarship Applied</option>
            <option value="REFUND_PROCESSED">Refund Processed</option>
            <option value="LATE_FEE_ASSESSED">Late Fee Assessed</option>
          </select>

          <label className="text-xs font-semibold text-slate-600 uppercase ml-2">Entity:</label>
          <select
            value={entityTypeFilter}
            onChange={(e) => { setEntityTypeFilter(e.target.value); setPage(1); }}
            className="input-field text-sm py-1.5 px-3 w-36"
          >
            <option value="">All Entities</option>
            <option value="Invoice">Invoice</option>
            <option value="Payment">Payment</option>
            <option value="Refund">Refund</option>
            <option value="Scholarship">Scholarship</option>
          </select>
        </div>
        <span className="text-xs text-slate-500 font-medium">{total} immutable events logged</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Event ID</th>
                <th className="px-6 py-3.5">Timestamp</th>
                <th className="px-6 py-3.5">Event Type</th>
                <th className="px-6 py-3.5">Target Entity</th>
                <th className="px-6 py-3.5">Debit / Credit Impact</th>
                <th className="px-6 py-3.5">Amount</th>
                <th className="px-6 py-3.5 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-normal text-slate-800">
              {loading ? (
                <tr><td colSpan="7" className="px-6 py-12 text-center text-slate-400">Loading immutable audit log...</td></tr>
              ) : events.length === 0 ? (
                <tr><td colSpan="7" className="px-6 py-12 text-center text-slate-400">No ledger events recorded.</td></tr>
              ) : (
                events.map((e) => {
                  const debit = isDebit(e.event_type);
                  return (
                    <tr key={e.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-6 py-4 font-mono text-xs font-semibold text-primary-700">{e.event_id}</td>
                      <td className="px-6 py-4 text-xs text-slate-500">
                        {new Date(e.event_timestamp || e.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-800 font-medium">
                          {e.event_type}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-semibold text-slate-900">{e.entity_type}</span>
                        <span className="font-mono text-xs text-slate-400 ml-1.5">#{e.entity_id}</span>
                      </td>
                      <td className="px-6 py-4">
                        {debit ? (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-rose-700">
                            <ArrowUpRight className="w-3.5 h-3.5" /> DEBIT (Receivable)
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700">
                            <ArrowDownRight className="w-3.5 h-3.5" /> CREDIT (Reduction)
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 font-mono text-xs font-bold text-slate-900">
                        {e.amount !== null && e.amount !== undefined ? formatCurrency(e.amount) : '—'}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => setSelectedEvent(e)}
                          className="px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 border border-slate-200 rounded hover:bg-slate-50"
                        >
                          Audit Payload
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        <div className="p-4 border-t border-slate-200">
          <Pagination currentPage={page} totalPages={pages} onPageChange={setPage} />
        </div>
      </div>

      {/* STUDENT STATEMENT MODAL */}
      <Modal
        isOpen={isStatementModalOpen}
        onClose={() => setIsStatementModalOpen(false)}
        title="Student Balance Statement"
      >
        <div className="space-y-4">
          <form onSubmit={handleFetchStatement} className="flex gap-2">
            <input
              type="number"
              required
              value={searchStudentId}
              onChange={(e) => setSearchStudentId(e.target.value)}
              placeholder="Enter Student Database ID (e.g. 1)"
              className="input-field flex-1 text-sm"
            />
            <button
              type="submit"
              disabled={statementLoading}
              className="btn-primary text-sm flex items-center gap-1.5"
            >
              <Search className="w-4 h-4" />
              {statementLoading ? 'Calculating...' : 'Fetch'}
            </button>
          </form>

          {statementError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
              {statementError}
            </div>
          )}

          {statement && (
            <div className="space-y-4 pt-2 border-t border-slate-100">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-slate-900">{statement.student_name}</h3>
                  <p className="font-mono text-xs text-slate-500">{statement.student_business_id}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500 uppercase font-semibold">Net Outstanding</p>
                  <p className={`text-xl font-bold font-mono ${parseFloat(statement.outstanding_balance) > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                    {formatCurrency(statement.outstanding_balance)}
                  </p>
                </div>
              </div>

              {/* KPI Matrix */}
              <div className="grid grid-cols-3 gap-2 bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
                <div>
                  <span className="text-slate-500 block">Gross Charges:</span>
                  <span className="font-bold text-slate-800 font-mono">{formatCurrency(statement.gross_charges)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Scholarships:</span>
                  <span className="font-bold text-emerald-700 font-mono">-{formatCurrency(statement.approved_scholarships)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Net Collectible:</span>
                  <span className="font-bold text-slate-900 font-mono">{formatCurrency(statement.net_collectible)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Late Fees:</span>
                  <span className="font-bold text-amber-700 font-mono">+{formatCurrency(statement.assessed_late_fees)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Total Payments:</span>
                  <span className="font-bold text-emerald-700 font-mono">-{formatCurrency(statement.total_payments)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Total Refunds:</span>
                  <span className="font-bold text-rose-700 font-mono">+{formatCurrency(statement.total_refunds)}</span>
                </div>
              </div>

              {/* Invoices List */}
              {statement.invoices && statement.invoices.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-700 uppercase mb-2">Invoice Summary</h4>
                  <div className="border border-slate-200 rounded-lg overflow-hidden max-h-48 overflow-y-auto">
                    <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
                      <thead className="bg-slate-50 text-slate-600 font-semibold">
                        <tr>
                          <th className="px-3 py-2">Invoice ID</th>
                          <th className="px-3 py-2">Cycle</th>
                          <th className="px-3 py-2">Net</th>
                          <th className="px-3 py-2">Paid</th>
                          <th className="px-3 py-2">Balance</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {statement.invoices.map((inv) => (
                          <tr key={inv.invoice_id}>
                            <td className="px-3 py-2 font-mono text-primary-700">{inv.invoice_id}</td>
                            <td className="px-3 py-2">{inv.billing_cycle}</td>
                            <td className="px-3 py-2 font-mono">{formatCurrency(inv.net_amount)}</td>
                            <td className="px-3 py-2 font-mono text-emerald-700">{formatCurrency(inv.paid_amount)}</td>
                            <td className="px-3 py-2 font-mono font-bold text-rose-700">{formatCurrency(inv.outstanding_balance)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex justify-end pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsStatementModalOpen(false)}
              className="btn-secondary text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </Modal>

      {/* AUDIT PAYLOAD MODAL */}
      <Modal
        isOpen={!!selectedEvent}
        onClose={() => setSelectedEvent(null)}
        title={`Audit Payload — ${selectedEvent?.event_id}`}
      >
        <div className="space-y-3">
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs space-y-1">
            <p><span className="font-semibold text-slate-600">Event Type:</span> {selectedEvent?.event_type}</p>
            <p><span className="font-semibold text-slate-600">Entity:</span> {selectedEvent?.entity_type} #{selectedEvent?.entity_id}</p>
            <p><span className="font-semibold text-slate-600">Previous State:</span> {selectedEvent?.previous_state || 'None'}</p>
            <p><span className="font-semibold text-slate-600">New State:</span> {selectedEvent?.new_state || 'None'}</p>
            <p><span className="font-semibold text-slate-600">Actor ID:</span> {selectedEvent?.actor_id || 'SYSTEM'}</p>
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase mb-1">Metadata JSON</h4>
            <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono overflow-x-auto max-h-60">
              {JSON.stringify(selectedEvent?.metadata_json || {}, null, 2)}
            </pre>
          </div>
          <div className="flex justify-end pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setSelectedEvent(null)}
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
