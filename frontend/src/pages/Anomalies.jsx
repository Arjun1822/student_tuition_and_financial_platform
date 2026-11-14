import React, { useState, useEffect } from 'react';
import { anomaliesApi } from '../api/anomalies';
import StatusBadge from '../components/common/StatusBadge';
import Pagination from '../components/common/Pagination';
import Modal from '../components/common/Modal';
import { AlertTriangle, Scan, CheckCircle, Eye, ShieldAlert, AlertOctagon, Info } from 'lucide-react';

export default function Anomalies() {
  const [anomalies, setAnomalies] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [issueTypeFilter, setIssueTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Scan State
  const [scanning, setScanning] = useState(false);

  // Resolve Modal
  const [resolveAnomalyItem, setResolveAnomalyItem] = useState(null);
  const [resolveStatus, setResolveStatus] = useState('RESOLVED');
  const [resolveNotes, setResolveNotes] = useState('');
  const [resolveSubmitting, setResolveSubmitting] = useState(false);
  const [resolveError, setResolveError] = useState(null);

  // Details Modal
  const [viewAnomaly, setViewAnomaly] = useState(null);

  const fetchAnomalies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await anomaliesApi.getAnomalies({
        page,
        page_size: 15,
        issue_type: issueTypeFilter || undefined,
        severity: severityFilter || undefined,
        resolution_status: statusFilter || undefined,
      });
      setAnomalies(data.items || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load anomalies');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, [page, issueTypeFilter, severityFilter, statusFilter]);

  const handleTriggerScan = async () => {
    setScanning(true);
    setError(null);
    setActionSuccess(null);
    try {
      const results = await anomaliesApi.triggerAnomalyScan();
      setActionSuccess(`Anomaly scan completed. ${results.length} active anomalies detected / updated.`);
      fetchAnomalies();
    } catch (err) {
      setError(err.response?.data?.detail || 'Anomaly scan execution failed');
    } finally {
      setScanning(false);
    }
  };

  const handleResolve = async (e) => {
    e.preventDefault();
    if (!resolveAnomalyItem) return;
    if (!resolveNotes || resolveNotes.length < 3) {
      setResolveError('Resolution notes are required (min 3 characters).');
      return;
    }
    setResolveSubmitting(true);
    setResolveError(null);
    try {
      await anomaliesApi.resolveAnomaly(resolveAnomalyItem.id, {
        resolution_status: resolveStatus,
        resolution_notes: resolveNotes,
      });
      setResolveAnomalyItem(null);
      setResolveNotes('');
      setActionSuccess(`Anomaly ${resolveAnomalyItem.anomaly_id} marked as ${resolveStatus}.`);
      fetchAnomalies();
    } catch (err) {
      setResolveError(err.response?.data?.detail || 'Failed to update anomaly status');
    } finally {
      setResolveSubmitting(false);
    }
  };

  const formatCurrency = (val) => {
    if (val === null || val === undefined) return '—';
    const num = parseFloat(val) || 0;
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Anomaly Detection & Exceptions</h1>
          <p className="text-sm text-slate-500 mt-1">
            Deterministic rule-based heuristics identifying financial leaks, orphaned ledger lines, and duplicate invoices.
          </p>
        </div>
        <button
          onClick={handleTriggerScan}
          disabled={scanning}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto"
        >
          <Scan className="w-4 h-4" />
          {scanning ? 'Running Heuristics Scan...' : 'Run Anomaly Scan'}
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
          <label className="text-xs font-semibold text-slate-600 uppercase">Issue Type:</label>
          <select
            value={issueTypeFilter}
            onChange={(e) => { setIssueTypeFilter(e.target.value); setPage(1); }}
            className="input-field text-sm py-1.5 px-3 w-56"
          >
            <option value="">All Issue Types</option>
            <option value="OVERPAYMENT">Overpayment</option>
            <option value="DUPLICATE_INVOICE">Duplicate Invoice</option>
            <option value="SCHOLARSHIP_EXCEEDS_CAP">Scholarship Exceeds Cap</option>
            <option value="INCORRECT_FEE_CALCULATION">Incorrect Fee Calculation</option>
            <option value="ORPHAN_PAYMENT">Orphan Payment</option>
          </select>

          <label className="text-xs font-semibold text-slate-600 uppercase ml-2">Severity:</label>
          <select
            value={severityFilter}
            onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
            className="input-field text-sm py-1.5 px-3 w-36"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <label className="text-xs font-semibold text-slate-600 uppercase ml-2">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="input-field text-sm py-1.5 px-3 w-36"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="RESOLVED">Resolved</option>
            <option value="IGNORED">Ignored</option>
          </select>
        </div>
        <span className="text-xs text-slate-500 font-medium">{total} total anomalies cataloged</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Anomaly ID</th>
                <th className="px-6 py-3.5">Severity</th>
                <th className="px-6 py-3.5">Issue Type</th>
                <th className="px-6 py-3.5">Target Entity</th>
                <th className="px-6 py-3.5">Expected vs Actual</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-normal text-slate-800">
              {loading ? (
                <tr><td colSpan="7" className="px-6 py-12 text-center text-slate-400">Loading anomalies...</td></tr>
              ) : anomalies.length === 0 ? (
                <tr><td colSpan="7" className="px-6 py-12 text-center text-slate-400">No anomalies detected. Run an anomaly scan to evaluate rules.</td></tr>
              ) : (
                anomalies.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs font-semibold text-primary-700">{a.anomaly_id}</td>
                    <td className="px-6 py-4"><StatusBadge status={a.severity} /></td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-slate-900">{a.issue_type}</span>
                      <p className="text-xs text-slate-500 max-w-xs truncate">{a.explanation}</p>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-700">
                      {a.entity_type} #{a.entity_id}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs">
                      <div><span className="text-slate-400">Exp:</span> {formatCurrency(a.expected_value)}</div>
                      <div><span className="text-slate-400">Act:</span> {formatCurrency(a.actual_value)}</div>
                    </td>
                    <td className="px-6 py-4"><StatusBadge status={a.resolution_status} /></td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setViewAnomaly(a)}
                          className="px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 border border-slate-200 rounded hover:bg-slate-50 flex items-center gap-1"
                        >
                          <Info className="w-3.5 h-3.5" /> Details
                        </button>
                        {a.resolution_status !== 'RESOLVED' && (
                          <button
                            onClick={() => { setResolveAnomalyItem(a); setResolveStatus('RESOLVED'); setResolveNotes(''); setResolveError(null); }}
                            className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold flex items-center gap-1"
                          >
                            <CheckCircle className="w-3.5 h-3.5" /> Resolve
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

      {/* RESOLVE MODAL */}
      <Modal
        isOpen={!!resolveAnomalyItem}
        onClose={() => setResolveAnomalyItem(null)}
        title={`Resolve Exception — ${resolveAnomalyItem?.anomaly_id}`}
      >
        <form onSubmit={handleResolve} className="space-y-4">
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
            <p><span className="font-semibold text-slate-700">Type:</span> {resolveAnomalyItem?.issue_type}</p>
            <p className="mt-1 text-slate-600">{resolveAnomalyItem?.explanation}</p>
          </div>
          {resolveError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
              {resolveError}
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Resolution Status *</label>
            <select
              value={resolveStatus}
              onChange={(e) => setResolveStatus(e.target.value)}
              className="input-field w-full text-sm"
            >
              <option value="RESOLVED">Resolved (Corrected in Ledger)</option>
              <option value="INVESTIGATING">Investigating (In Progress)</option>
              <option value="IGNORED">Ignored (False Positive / Accepted Risk)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Resolution Notes *</label>
            <textarea
              rows="3"
              required
              value={resolveNotes}
              onChange={(e) => setResolveNotes(e.target.value)}
              className="input-field w-full text-sm"
              placeholder="Detail actions taken to resolve or remediate this exception..."
            />
          </div>
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setResolveAnomalyItem(null)}
              className="btn-secondary text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={resolveSubmitting}
              className="btn-primary text-sm"
            >
              {resolveSubmitting ? 'Saving...' : 'Save Resolution'}
            </button>
          </div>
        </form>
      </Modal>

      {/* VIEW DETAILS MODAL */}
      <Modal
        isOpen={!!viewAnomaly}
        onClose={() => setViewAnomaly(null)}
        title={`Anomaly Details — ${viewAnomaly?.anomaly_id}`}
      >
        <div className="space-y-3">
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-slate-600">Issue Classification:</span>
              <span className="font-bold text-slate-900">{viewAnomaly?.issue_type}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-slate-600">Severity Level:</span>
              <StatusBadge status={viewAnomaly?.severity} />
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-slate-600">Target Entity:</span>
              <span className="font-mono text-primary-700">{viewAnomaly?.entity_type} #{viewAnomaly?.entity_id}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-slate-600">Expected Amount:</span>
              <span className="font-mono font-bold">{formatCurrency(viewAnomaly?.expected_value)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-slate-600">Actual Amount:</span>
              <span className="font-mono font-bold text-rose-700">{formatCurrency(viewAnomaly?.actual_value)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-slate-600">Detection Timestamp:</span>
              <span className="text-slate-500">{new Date(viewAnomaly?.detection_timestamp || viewAnomaly?.created_at).toLocaleString()}</span>
            </div>
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase mb-1">Diagnostic Root Cause</h4>
            <p className="p-3 bg-slate-100 rounded-lg text-xs text-slate-700 leading-relaxed">
              {viewAnomaly?.explanation}
            </p>
          </div>
          {viewAnomaly?.resolution_notes && (
            <div>
              <h4 className="text-xs font-bold text-slate-700 uppercase mb-1">Audit Resolution Notes</h4>
              <p className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800">
                {viewAnomaly.resolution_notes}
              </p>
            </div>
          )}
          <div className="flex justify-end pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setViewAnomaly(null)}
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

