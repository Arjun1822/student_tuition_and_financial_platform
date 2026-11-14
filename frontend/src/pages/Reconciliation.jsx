import React, { useState, useEffect } from 'react';
import { reconciliationApi } from '../api/reconciliation';
import StatusBadge from '../components/common/StatusBadge';
import Pagination from '../components/common/Pagination';
import Modal from '../components/common/Modal';
import { Scale, Play, CheckCircle2, AlertTriangle, Eye, RefreshCw, Filter } from 'lucide-react';

export default function Reconciliation() {
  const [runs, setRuns] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Trigger Modal
  const [isTriggerModalOpen, setIsTriggerModalOpen] = useState(false);
  const [triggerSubmitting, setTriggerSubmitting] = useState(false);
  const [triggerError, setTriggerError] = useState(null);
  const [formData, setFormData] = useState({
    term_id: '',
    program_id: '',
    notes: '',
  });

  // Results View Modal
  const [selectedRun, setSelectedRun] = useState(null);
  const [results, setResults] = useState([]);
  const [resultsLoading, setResultsLoading] = useState(false);
  const [resultsFilter, setResultsFilter] = useState('');

  const fetchRuns = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await reconciliationApi.getReconciliationRuns({
        page,
        page_size: 15,
        status: statusFilter || undefined,
      });
      setRuns(data.items || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load reconciliation runs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [page, statusFilter]);

  const handleTrigger = async (e) => {
    e.preventDefault();
    setTriggerSubmitting(true);
    setTriggerError(null);
    try {
      const run = await reconciliationApi.triggerReconciliation({
        term_id: formData.term_id ? parseInt(formData.term_id, 10) : undefined,
        program_id: formData.program_id ? parseInt(formData.program_id, 10) : undefined,
        notes: formData.notes || undefined,
      });
      setIsTriggerModalOpen(false);
      setFormData({ term_id: '', program_id: '', notes: '' });
      setActionSuccess(`Reconciliation run ${run.run_id} completed: ${run.matched_count} matched, ${run.mismatched_count} mismatched.`);
      fetchRuns();
    } catch (err) {
      setTriggerError(err.response?.data?.detail || 'Failed to trigger reconciliation');
    } finally {
      setTriggerSubmitting(false);
    }
  };

  const handleViewResults = async (run) => {
    setSelectedRun(run);
    setResultsLoading(true);
    try {
      const data = await reconciliationApi.getReconciliationResults(run.id, {
        page_size: 100,
        status: resultsFilter || undefined,
      });
      setResults(data.items || (Array.isArray(data) ? data : []));
    } catch (err) {
      console.error(err);
      setResults([]);
    } finally {
      setResultsLoading(false);
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
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Financial Reconciliation</h1>
          <p className="text-sm text-slate-500 mt-1">
            Expected vs actual receivable matching, line-item ledger balance checks, and discrepancy reports.
          </p>
        </div>
        <button
          onClick={() => setIsTriggerModalOpen(true)}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto"
        >
          <Play className="w-4 h-4" />
          Run Reconciliation
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
          <label className="text-xs font-semibold text-slate-600 uppercase">Run Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="input-field text-sm py-1.5 px-3 w-40"
          >
            <option value="">All Runs</option>
            <option value="COMPLETED">Completed</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
        <span className="text-xs text-slate-500 font-medium">{total} reconciliation runs executed</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Run ID</th>
                <th className="px-6 py-3.5">Execution Date</th>
                <th className="px-6 py-3.5">Audited Invoices</th>
                <th className="px-6 py-3.5">Matched</th>
                <th className="px-6 py-3.5">Mismatched</th>
                <th className="px-6 py-3.5">Exceptions</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-normal text-slate-800">
              {loading ? (
                <tr><td colSpan="8" className="px-6 py-12 text-center text-slate-400">Loading reconciliation runs...</td></tr>
              ) : runs.length === 0 ? (
                <tr><td colSpan="8" className="px-6 py-12 text-center text-slate-400">No reconciliation runs found. Trigger a run to begin audit.</td></tr>
              ) : (
                runs.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs font-semibold text-primary-700">{r.run_id}</td>
                    <td className="px-6 py-4 text-xs text-slate-500">
                      {new Date(r.run_date || r.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs font-semibold text-slate-900">{r.total_invoices}</td>
                    <td className="px-6 py-4 font-mono text-xs font-bold text-emerald-700">{r.matched_count}</td>
                    <td className="px-6 py-4 font-mono text-xs font-bold text-rose-700">{r.mismatched_count}</td>
                    <td className="px-6 py-4 font-mono text-xs font-bold text-amber-700">{r.exception_count}</td>
                    <td className="px-6 py-4"><StatusBadge status={r.status} /></td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleViewResults(r)}
                        className="btn-secondary text-xs py-1 px-2.5 flex items-center gap-1.5 ml-auto"
                      >
                        <Eye className="w-3.5 h-3.5" /> View Discrepancies
                      </button>
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

      {/* TRIGGER RUN MODAL */}
      <Modal
        isOpen={isTriggerModalOpen}
        onClose={() => setIsTriggerModalOpen(false)}
        title="Execute Reconciliation Run"
      >
        <form onSubmit={handleTrigger} className="space-y-4">
          <p className="text-xs text-slate-500">
            Reconciles invoice line-item gross charges, discounts, and payments against double-entry ledger totals.
          </p>
          {triggerError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
              {triggerError}
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Term Filter (Optional)</label>
              <input
                type="number"
                value={formData.term_id}
                onChange={(e) => setFormData({ ...formData, term_id: e.target.value })}
                className="input-field w-full text-sm"
                placeholder="All terms if blank"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Program Filter (Optional)</label>
              <input
                type="number"
                value={formData.program_id}
                onChange={(e) => setFormData({ ...formData, program_id: e.target.value })}
                className="input-field w-full text-sm"
                placeholder="All programs if blank"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Audit Notes (Optional)</label>
            <textarea
              rows="2"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="input-field w-full text-sm"
              placeholder="e.g. End of Month Fall 2026 Batch Audit"
            />
          </div>
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsTriggerModalOpen(false)}
              className="btn-secondary text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={triggerSubmitting}
              className="btn-primary text-sm flex items-center gap-1.5"
            >
              <Play className="w-4 h-4" />
              {triggerSubmitting ? 'Running Audit...' : 'Execute Run'}
            </button>
          </div>
        </form>
      </Modal>

      {/* VIEW RESULTS MODAL */}
      <Modal
        isOpen={!!selectedRun}
        onClose={() => setSelectedRun(null)}
        title={`Reconciliation Audit Results — ${selectedRun?.run_id}`}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-2 bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
            <div>
              <span className="text-slate-500 block">Total Audited:</span>
              <span className="font-bold text-slate-900 font-mono">{selectedRun?.total_invoices}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Matched:</span>
              <span className="font-bold text-emerald-700 font-mono">{selectedRun?.matched_count}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Mismatched:</span>
              <span className="font-bold text-rose-700 font-mono">{selectedRun?.mismatched_count}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Exceptions:</span>
              <span className="font-bold text-amber-700 font-mono">{selectedRun?.exception_count}</span>
            </div>
          </div>

          {resultsLoading ? (
            <p className="text-center py-8 text-slate-400 text-sm">Loading audit line items...</p>
          ) : results.length === 0 ? (
            <p className="text-center py-8 text-slate-400 text-sm">No discrepancy items returned for this run.</p>
          ) : (
            <div className="border border-slate-200 rounded-lg overflow-hidden max-h-80 overflow-y-auto">
              <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold sticky top-0">
                  <tr>
                    <th className="px-3 py-2">Entity</th>
                    <th className="px-3 py-2">Expected</th>
                    <th className="px-3 py-2">Actual</th>
                    <th className="px-3 py-2">Difference</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Exception Note</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {results.map((item) => (
                    <tr key={item.id} className={item.status === 'MISMATCHED' ? 'bg-rose-50/50' : ''}>
                      <td className="px-3 py-2 font-mono text-primary-700">
                        {item.entity_type} #{item.entity_id}
                      </td>
                      <td className="px-3 py-2 font-mono">{formatCurrency(item.expected_amount)}</td>
                      <td className="px-3 py-2 font-mono">{formatCurrency(item.actual_amount)}</td>
                      <td className={`px-3 py-2 font-mono font-bold ${parseFloat(item.difference) !== 0 ? 'text-rose-700' : 'text-slate-600'}`}>
                        {formatCurrency(item.difference)}
                      </td>
                      <td className="px-3 py-2"><StatusBadge status={item.status} /></td>
                      <td className="px-3 py-2 text-slate-500 max-w-xs truncate">
                        {item.exception_type ? `[${item.exception_type}] ` : ''}{item.notes || '—'}
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
              onClick={() => setSelectedRun(null)}
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

