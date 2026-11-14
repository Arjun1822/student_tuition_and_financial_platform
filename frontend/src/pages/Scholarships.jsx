import React, { useState, useEffect } from 'react';
import { scholarshipsApi } from '../api/scholarships';
import { studentsApi } from '../api/students';
import StatusBadge from '../components/common/StatusBadge';
import Pagination from '../components/common/Pagination';
import Modal from '../components/common/Modal';
import { Award, Plus, CheckCircle, XCircle, Calculator, Search, Filter } from 'lucide-react';

export default function Scholarships() {
  const [activeTab, setActiveTab] = useState('programs'); // 'programs' | 'awards'

  // Programs state
  const [programs, setPrograms] = useState([]);
  const [progTotal, setProgTotal] = useState(0);
  const [progPage, setProgPage] = useState(1);
  const [progPages, setProgPages] = useState(1);
  const [progTypeFilter, setProgTypeFilter] = useState('');
  const [progStatusFilter, setProgStatusFilter] = useState('');

  // Awards/Eligibilities state
  const [awards, setAwards] = useState([]);
  const [awardTotal, setAwardTotal] = useState(0);
  const [awardPage, setAwardPage] = useState(1);
  const [awardPages, setAwardPages] = useState(1);
  const [awardStatusFilter, setAwardStatusFilter] = useState('');

  // Common UI state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // New Program Modal
  const [isProgModalOpen, setIsProgModalOpen] = useState(false);
  const [progSubmitting, setProgSubmitting] = useState(false);
  const [progFormError, setProgFormError] = useState(null);
  const [progFormData, setProgFormData] = useState({
    name: '',
    description: '',
    scholarship_type: 'MERIT',
    percentage: '',
    max_amount: '',
    min_gpa: '',
    total_budget: '',
    academic_year: '2026-2027',
  });

  // Evaluate Eligibility Modal
  const [isEvalModalOpen, setIsEvalModalOpen] = useState(false);
  const [evalSubmitting, setEvalSubmitting] = useState(false);
  const [evalError, setEvalError] = useState(null);
  const [evalResult, setEvalResult] = useState(null);
  const [evalFormData, setEvalFormData] = useState({
    student_id: '',
    term_id: '1',
  });

  // Action Modals (Approve / Reject)
  const [actionItem, setActionItem] = useState(null);
  const [actionType, setActionType] = useState(null); // 'approve' | 'reject'
  const [actionAmount, setActionAmount] = useState('');
  const [actionReason, setActionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchPrograms = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await scholarshipsApi.getScholarships({
        page: progPage,
        page_size: 15,
        scholarship_type: progTypeFilter || undefined,
        status: progStatusFilter || undefined,
      });
      setPrograms(data.items || []);
      setProgTotal(data.total || 0);
      setProgPages(data.pages || 1);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load scholarship schemes');
    } finally {
      setLoading(false);
    }
  };

  const fetchAwards = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await scholarshipsApi.getEligibilities({
        page: awardPage,
        page_size: 15,
        status: awardStatusFilter || undefined,
      });
      setAwards(data.items || []);
      setAwardTotal(data.total || 0);
      setAwardPages(data.pages || 1);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load scholarship awards');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'programs') {
      fetchPrograms();
    } else {
      fetchAwards();
    }
  }, [activeTab, progPage, progTypeFilter, progStatusFilter, awardPage, awardStatusFilter]);

  const handleCreateProgram = async (e) => {
    e.preventDefault();
    setProgSubmitting(true);
    setProgFormError(null);
    try {
      await scholarshipsApi.createScholarship({
        name: progFormData.name,
        description: progFormData.description || null,
        scholarship_type: progFormData.scholarship_type,
        percentage: parseFloat(progFormData.percentage),
        max_amount: parseFloat(progFormData.max_amount),
        min_gpa: progFormData.min_gpa ? parseFloat(progFormData.min_gpa) : null,
        total_budget: parseFloat(progFormData.total_budget),
        academic_year: progFormData.academic_year,
      });
      setIsProgModalOpen(false);
      setProgFormData({
        name: '',
        description: '',
        scholarship_type: 'MERIT',
        percentage: '',
        max_amount: '',
        min_gpa: '',
        total_budget: '',
        academic_year: '2026-2027',
      });
      setActionSuccess('Scholarship scheme created successfully.');
      fetchPrograms();
    } catch (err) {
      setProgFormError(err.response?.data?.detail || 'Failed to create scholarship program');
    } finally {
      setProgSubmitting(false);
    }
  };

  const handleEvaluate = async (e) => {
    e.preventDefault();
    setEvalSubmitting(true);
    setEvalError(null);
    setEvalResult(null);
    try {
      const res = await scholarshipsApi.evaluateScholarships({
        student_id: parseInt(evalFormData.student_id, 10),
        term_id: parseInt(evalFormData.term_id, 10),
      });
      setEvalResult(res);
      setActionSuccess('Scholarship evaluation complete.');
      if (activeTab === 'awards') fetchAwards();
    } catch (err) {
      setEvalError(err.response?.data?.detail || 'Evaluation failed. Verify student and term IDs.');
    } finally {
      setEvalSubmitting(false);
    }
  };

  const handleApprove = async () => {
    if (!actionItem) return;
    setActionLoading(true);
    try {
      await scholarshipsApi.approveEligibility(actionItem.id, {
        approved_amount: actionAmount ? parseFloat(actionAmount) : undefined,
        notes: actionReason || 'Approved via financial portal',
      });
      setActionItem(null);
      setActionSuccess(`Award ${actionItem.eligibility_id} approved successfully.`);
      fetchAwards();
    } catch (err) {
      setError(err.response?.data?.detail || 'Approval failed');
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
      await scholarshipsApi.rejectEligibility(actionItem.id, {
        reason: actionReason,
      });
      setActionItem(null);
      setActionSuccess(`Award ${actionItem.eligibility_id} rejected.`);
      fetchAwards();
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
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Scholarships & Grants</h1>
          <p className="text-sm text-slate-500 mt-1">
            Institutional endowment schemes, criteria-based evaluation engine, and award governance.
          </p>
        </div>
        <div className="flex items-center gap-3 self-start sm:self-auto">
          <button
            onClick={() => { setIsEvalModalOpen(true); setEvalResult(null); }}
            className="btn-secondary flex items-center gap-2"
          >
            <Calculator className="w-4 h-4" />
            Evaluate Eligibility
          </button>
          <button
            onClick={() => setIsProgModalOpen(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Scholarship
          </button>
        </div>
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

      {/* Tabs */}
      <div className="border-b border-slate-200 flex gap-6">
        <button
          onClick={() => setActiveTab('programs')}
          className={`pb-3 text-sm font-semibold transition-colors flex items-center gap-2 border-b-2 ${
            activeTab === 'programs'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Award className="w-4 h-4" />
          Scholarship Programs ({progTotal})
        </button>
        <button
          onClick={() => setActiveTab('awards')}
          className={`pb-3 text-sm font-semibold transition-colors flex items-center gap-2 border-b-2 ${
            activeTab === 'awards'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <CheckCircle className="w-4 h-4" />
          Award Approvals & Applications ({awardTotal})
        </button>
      </div>

      {/* TAB 1: PROGRAMS */}
      {activeTab === 'programs' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap gap-4 items-center justify-between">
            <div className="flex items-center gap-3">
              <label className="text-xs font-semibold text-slate-600 uppercase">Type:</label>
              <select
                value={progTypeFilter}
                onChange={(e) => { setProgTypeFilter(e.target.value); setProgPage(1); }}
                className="input-field text-sm py-1.5 px-3 w-40"
              >
                <option value="">All Types</option>
                <option value="MERIT">Merit</option>
                <option value="NEED_BASED">Need Based</option>
                <option value="PROGRAM_SPECIFIC">Program Specific</option>
                <option value="ATHLETIC">Athletic</option>
                <option value="SPECIAL">Special</option>
              </select>

              <label className="text-xs font-semibold text-slate-600 uppercase ml-2">Status:</label>
              <select
                value={progStatusFilter}
                onChange={(e) => { setProgStatusFilter(e.target.value); setProgPage(1); }}
                className="input-field text-sm py-1.5 px-3 w-36"
              >
                <option value="">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
                <option value="EXHAUSTED">Exhausted</option>
              </select>
            </div>
            <span className="text-xs text-slate-500 font-medium">{progTotal} total schemes configured</span>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3.5">Scheme ID</th>
                    <th className="px-6 py-3.5">Program Name</th>
                    <th className="px-6 py-3.5">Type</th>
                    <th className="px-6 py-3.5">Benefit</th>
                    <th className="px-6 py-3.5">Total Budget</th>
                    <th className="px-6 py-3.5">Awarded</th>
                    <th className="px-6 py-3.5">Remaining</th>
                    <th className="px-6 py-3.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-normal text-slate-800">
                  {loading ? (
                    <tr><td colSpan="8" className="px-6 py-12 text-center text-slate-400">Loading programs...</td></tr>
                  ) : programs.length === 0 ? (
                    <tr><td colSpan="8" className="px-6 py-12 text-center text-slate-400">No scholarship programs found.</td></tr>
                  ) : (
                    programs.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-6 py-4 font-mono text-xs font-semibold text-primary-700">{p.scholarship_id}</td>
                        <td className="px-6 py-4 font-medium text-slate-900">
                          {p.name}
                          {p.academic_year && <span className="ml-2 text-xs text-slate-400 font-normal">({p.academic_year})</span>}
                        </td>
                        <td className="px-6 py-4">
                          <span className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-700 font-medium">{p.scholarship_type}</span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="font-semibold text-emerald-700">{p.percentage}%</span>
                          <span className="text-xs text-slate-400 ml-1">cap {formatCurrency(p.max_amount)}</span>
                        </td>
                        <td className="px-6 py-4 font-mono text-xs">{formatCurrency(p.total_budget)}</td>
                        <td className="px-6 py-4 font-mono text-xs text-amber-700">{formatCurrency(p.awarded_amount)}</td>
                        <td className="px-6 py-4 font-mono text-xs font-semibold text-emerald-700">{formatCurrency(p.remaining_budget)}</td>
                        <td className="px-6 py-4"><StatusBadge status={p.status} /></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <div className="p-4 border-t border-slate-200">
              <Pagination currentPage={progPage} totalPages={progPages} onPageChange={setProgPage} />
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: AWARDS & APPLICATIONS */}
      {activeTab === 'awards' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap gap-4 items-center justify-between">
            <div className="flex items-center gap-3">
              <label className="text-xs font-semibold text-slate-600 uppercase">Status:</label>
              <select
                value={awardStatusFilter}
                onChange={(e) => { setAwardStatusFilter(e.target.value); setAwardPage(1); }}
                className="input-field text-sm py-1.5 px-3 w-40"
              >
                <option value="">All Statuses</option>
                <option value="PENDING">Pending Review</option>
                <option value="APPROVED">Approved</option>
                <option value="REJECTED">Rejected</option>
                <option value="APPLIED">Applied</option>
              </select>
            </div>
            <span className="text-xs text-slate-500 font-medium">{awardTotal} applications recorded</span>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3.5">Award ID</th>
                    <th className="px-6 py-3.5">Student</th>
                    <th className="px-6 py-3.5">Scholarship Scheme</th>
                    <th className="px-6 py-3.5">Calculated</th>
                    <th className="px-6 py-3.5">Approved Amount</th>
                    <th className="px-6 py-3.5">Status</th>
                    <th className="px-6 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-normal text-slate-800">
                  {loading ? (
                    <tr><td colSpan="7" className="px-6 py-12 text-center text-slate-400">Loading awards...</td></tr>
                  ) : awards.length === 0 ? (
                    <tr><td colSpan="7" className="px-6 py-12 text-center text-slate-400">No scholarship records found.</td></tr>
                  ) : (
                    awards.map((a) => (
                      <tr key={a.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-6 py-4 font-mono text-xs font-semibold text-primary-700">{a.eligibility_id}</td>
                        <td className="px-6 py-4">
                          <p className="font-semibold text-slate-900">{a.student_name || `Student #${a.student_id}`}</p>
                          <p className="font-mono text-xs text-slate-400">{a.student_business_id}</p>
                        </td>
                        <td className="px-6 py-4">
                          <p className="font-medium text-slate-900">{a.scholarship_name || `Scholarship #${a.scholarship_id}`}</p>
                          <p className="text-xs text-slate-400">{a.scholarship_percentage}% of eligible fees</p>
                        </td>
                        <td className="px-6 py-4 font-mono text-xs text-slate-700">{formatCurrency(a.calculated_amount)}</td>
                        <td className="px-6 py-4 font-mono text-xs font-semibold text-emerald-700">
                          {formatCurrency(a.approved_amount || a.calculated_amount)}
                        </td>
                        <td className="px-6 py-4"><StatusBadge status={a.status} /></td>
                        <td className="px-6 py-4 text-right">
                          {a.status === 'PENDING' ? (
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => { setActionItem(a); setActionType('approve'); setActionAmount(a.calculated_amount); setActionReason(''); }}
                                className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold flex items-center gap-1"
                              >
                                <CheckCircle className="w-3.5 h-3.5" /> Approve
                              </button>
                              <button
                                onClick={() => { setActionItem(a); setActionType('reject'); setActionReason(''); }}
                                className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded text-xs font-semibold flex items-center gap-1"
                              >
                                <XCircle className="w-3.5 h-3.5" /> Reject
                              </button>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400 italic">No action required</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <div className="p-4 border-t border-slate-200">
              <Pagination currentPage={awardPage} totalPages={awardPages} onPageChange={setAwardPage} />
            </div>
          </div>
        </div>
      )}

      {/* CREATE PROGRAM MODAL */}
      <Modal
        isOpen={isProgModalOpen}
        onClose={() => setIsProgModalOpen(false)}
        title="Create Scholarship Scheme"
      >
        <form onSubmit={handleCreateProgram} className="space-y-4">
          {progFormError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
              {progFormError}
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Scheme Name *</label>
            <input
              type="text"
              required
              value={progFormData.name}
              onChange={(e) => setProgFormData({ ...progFormData, name: e.target.value })}
              className="input-field w-full text-sm"
              placeholder="e.g. Merit Excellence Endowment"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Scholarship Type *</label>
            <select
              value={progFormData.scholarship_type}
              onChange={(e) => setProgFormData({ ...progFormData, scholarship_type: e.target.value })}
              className="input-field w-full text-sm"
            >
              <option value="MERIT">Merit</option>
              <option value="NEED_BASED">Need Based</option>
              <option value="PROGRAM_SPECIFIC">Program Specific</option>
              <option value="ATHLETIC">Athletic</option>
              <option value="SPECIAL">Special</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Percentage Benefit (%) *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                required
                value={progFormData.percentage}
                onChange={(e) => setProgFormData({ ...progFormData, percentage: e.target.value })}
                className="input-field w-full text-sm"
                placeholder="50.00"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Max Cap Amount (₹) *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={progFormData.max_amount}
                onChange={(e) => setProgFormData({ ...progFormData, max_amount: e.target.value })}
                className="input-field w-full text-sm"
                placeholder="100000.00"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Total Budget (₹) *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={progFormData.total_budget}
                onChange={(e) => setProgFormData({ ...progFormData, total_budget: e.target.value })}
                className="input-field w-full text-sm"
                placeholder="10000000.00"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Academic Year *</label>
              <input
                type="text"
                required
                value={progFormData.academic_year}
                onChange={(e) => setProgFormData({ ...progFormData, academic_year: e.target.value })}
                className="input-field w-full text-sm"
                placeholder="2026-2027"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Min GPA Threshold (Optional)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="10"
              value={progFormData.min_gpa}
              onChange={(e) => setProgFormData({ ...progFormData, min_gpa: e.target.value })}
              className="input-field w-full text-sm"
              placeholder="8.50"
            />
          </div>
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsProgModalOpen(false)}
              className="btn-secondary text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={progSubmitting}
              className="btn-primary text-sm"
            >
              {progSubmitting ? 'Creating Scheme...' : 'Save Scheme'}
            </button>
          </div>
        </form>
      </Modal>

      {/* EVALUATE ELIGIBILITY MODAL */}
      <Modal
        isOpen={isEvalModalOpen}
        onClose={() => setIsEvalModalOpen(false)}
        title="Run Scholarship Eligibility Engine"
      >
        <form onSubmit={handleEvaluate} className="space-y-4">
          <p className="text-xs text-slate-500">
            Triggers rule evaluation against active enrollment fee schedules, family income, and academic GPA.
          </p>
          {evalError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
              {evalError}
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Student Primary Database ID *</label>
            <input
              type="number"
              required
              value={evalFormData.student_id}
              onChange={(e) => setEvalFormData({ ...evalFormData, student_id: e.target.value })}
              className="input-field w-full text-sm"
              placeholder="e.g. 1"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Academic Term ID *</label>
            <input
              type="number"
              required
              value={evalFormData.term_id}
              onChange={(e) => setEvalFormData({ ...evalFormData, term_id: e.target.value })}
              className="input-field w-full text-sm"
              placeholder="e.g. 1"
            />
          </div>
          {evalResult && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
              <p className="font-semibold text-slate-800">Engine Evaluation Result:</p>
              <pre className="font-mono text-[11px] text-slate-600 overflow-x-auto max-h-40">
                {JSON.stringify(evalResult, null, 2)}
              </pre>
            </div>
          )}
          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsEvalModalOpen(false)}
              className="btn-secondary text-sm"
            >
              Close
            </button>
            <button
              type="submit"
              disabled={evalSubmitting}
              className="btn-primary text-sm flex items-center gap-2"
            >
              <Calculator className="w-4 h-4" />
              {evalSubmitting ? 'Evaluating...' : 'Run Evaluation'}
            </button>
          </div>
        </form>
      </Modal>

      {/* APPROVE / REJECT MODAL */}
      <Modal
        isOpen={!!actionItem}
        onClose={() => setActionItem(null)}
        title={actionType === 'approve' ? 'Approve Scholarship Award' : 'Reject Scholarship Award'}
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            {actionType === 'approve'
              ? `Authorize financial disbursement for award ${actionItem?.eligibility_id}.`
              : `Reject application ${actionItem?.eligibility_id}.`}
          </p>
          {actionType === 'approve' ? (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Approved Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                value={actionAmount}
                onChange={(e) => setActionAmount(e.target.value)}
                className="input-field w-full text-sm"
              />
            </div>
          ) : null}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {actionType === 'approve' ? 'Review Notes' : 'Rejection Reason *'}
            </label>
            <textarea
              rows="3"
              value={actionReason}
              onChange={(e) => setActionReason(e.target.value)}
              className="input-field w-full text-sm"
              placeholder={actionType === 'approve' ? 'Optional audit comments...' : 'Enter reason for rejection...'}
            />
          </div>
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
              onClick={actionType === 'approve' ? handleApprove : handleReject}
              className={actionType === 'approve' ? 'btn-primary text-sm' : 'px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-sm font-semibold'}
            >
              {actionLoading ? 'Processing...' : actionType === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
