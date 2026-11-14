import React, { useState, useEffect } from 'react';
import { enrollmentsApi } from '../api/enrollments';
import { studentsApi } from '../api/students';
import { programsApi } from '../api/programs';
import StatusBadge from '../components/common/StatusBadge';
import Pagination from '../components/common/Pagination';
import Modal from '../components/common/Modal';
import { FileSpreadsheet, Plus, AlertCircle, Ban, ArrowDownRight } from 'lucide-react';

export default function Enrollments() {
  const [enrollments, setEnrollments] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form dropdown data
  const [studentsList, setStudentsList] = useState([]);
  const [programsList, setProgramsList] = useState([]);

  // Create Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [formData, setFormData] = useState({
    student_id: '',
    program_id: '',
    term_id: 1,
    enrollment_date: '2026-01-15',
  });

  // Action Modal (Cancel/Withdraw)
  const [actionModal, setActionModal] = useState({
    isOpen: false,
    enrollmentId: null,
    actionType: null, // 'cancel' | 'withdraw'
    reason: '',
  });

  const fetchEnrollments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await enrollmentsApi.getEnrollments({
        page,
        page_size: 15,
        status: statusFilter || undefined,
      });
      setEnrollments(data.items);
      setTotal(data.total);
      setPages(data.pages);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load enrollments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    studentsApi.getStudents({ page_size: 100 })
      .then((d) => setStudentsList(d.items || []))
      .catch((e) => console.error(e));
    programsApi.getPrograms({ page_size: 100 })
      .then((d) => setProgramsList(d.items || []))
      .catch((e) => console.error(e));
  }, []);

  useEffect(() => {
    fetchEnrollments();
  }, [page, statusFilter]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      await enrollmentsApi.createEnrollment({
        student_id: parseInt(formData.student_id, 10),
        program_id: parseInt(formData.program_id, 10),
        term_id: parseInt(formData.term_id, 10),
        enrollment_date: formData.enrollment_date,
      });
      setIsModalOpen(false);
      fetchEnrollments();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create enrollment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleActionSubmit = async (e) => {
    e.preventDefault();
    try {
      if (actionModal.actionType === 'cancel') {
        await enrollmentsApi.cancelEnrollment(actionModal.enrollmentId, actionModal.reason);
      } else {
        await enrollmentsApi.withdrawEnrollment(actionModal.enrollmentId, actionModal.reason);
      }
      setActionModal({ isOpen: false, enrollmentId: null, actionType: null, reason: '' });
      fetchEnrollments();
    } catch (err) {
      alert(err.response?.data?.detail || 'Action failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Student Enrollments</h1>
          <p className="text-sm text-slate-500 mt-1">
            Program enrollments, lifecycle transitions, cancellations, and term withdrawals.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Enroll Student
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
          <option value="ACTIVE">Active</option>
          <option value="PENDING">Pending</option>
          <option value="CANCELLED">Cancelled</option>
          <option value="WITHDRAWN">Withdrawn</option>
          <option value="COMPLETED">Completed</option>
        </select>
      </div>

      {/* Enrollments Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">Loading enrollments...</div>
        ) : error ? (
          <div className="p-8 text-center text-rose-600 flex items-center justify-center gap-2">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Enrollment ID</th>
                  <th className="px-6 py-3.5">Student</th>
                  <th className="px-6 py-3.5">Program</th>
                  <th className="px-6 py-3.5">Term</th>
                  <th className="px-6 py-3.5">Date</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {enrollments.map((enr) => (
                  <tr key={enr.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-slate-900">
                      {enr.enrollment_id}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-slate-900">
                        {enr.student?.first_name} {enr.student?.last_name}
                      </span>
                      <p className="text-xs text-slate-500 font-mono">{enr.student?.student_id}</p>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-medium text-slate-800">{enr.program?.code}</span>
                      <p className="text-xs text-slate-500">{enr.program?.name}</p>
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-700">
                      {enr.term?.name || enr.term?.term_id}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500">{enr.enrollment_date}</td>
                    <td className="px-6 py-4">
                      <StatusBadge status={enr.status} />
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      {enr.status === 'ACTIVE' && (
                        <>
                          <button
                            onClick={() =>
                              setActionModal({
                                isOpen: true,
                                enrollmentId: enr.id,
                                actionType: 'withdraw',
                                reason: '',
                              })
                            }
                            className="inline-flex items-center gap-1 text-xs font-semibold text-purple-600 hover:text-purple-700"
                          >
                            <ArrowDownRight className="w-3.5 h-3.5" />
                            Withdraw
                          </button>
                          <button
                            onClick={() =>
                              setActionModal({
                                isOpen: true,
                                enrollmentId: enr.id,
                                actionType: 'cancel',
                                reason: '',
                              })
                            }
                            className="inline-flex items-center gap-1 text-xs font-semibold text-rose-600 hover:text-rose-700"
                          >
                            <Ban className="w-3.5 h-3.5" />
                            Cancel
                          </button>
                        </>
                      )}
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

      {/* Enroll Student Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Enroll Student in Academic Program"
      >
        {formError && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{formError}</span>
          </div>
        )}

        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Select Student *
            </label>
            <select
              required
              value={formData.student_id}
              onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
            >
              <option value="">Choose Student</option>
              {studentsList.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.student_id} - {s.first_name} {s.last_name} ({s.email})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Select Program *
            </label>
            <select
              required
              value={formData.program_id}
              onChange={(e) => setFormData({ ...formData, program_id: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
            >
              <option value="">Choose Program</option>
              {programsList.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code} - {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Term ID *
              </label>
              <input
                type="number"
                required
                value={formData.term_id}
                onChange={(e) => setFormData({ ...formData, term_id: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Enrollment Date *
              </label>
              <input
                type="date"
                required
                value={formData.enrollment_date}
                onChange={(e) => setFormData({ ...formData, enrollment_date: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
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
              {submitting ? 'Enrolling...' : 'Submit Enrollment'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Action Dialog (Cancel/Withdraw) */}
      <Modal
        isOpen={actionModal.isOpen}
        onClose={() => setActionModal({ isOpen: false, enrollmentId: null, actionType: null, reason: '' })}
        title={`${actionModal.actionType === 'cancel' ? 'Cancel Enrollment' : 'Withdraw Student from Term'}`}
      >
        <form onSubmit={handleActionSubmit} className="space-y-4">
          <p className="text-xs text-slate-600">
            Please document the administrative reason for this {actionModal.actionType} action. This
            will be permanently logged in the financial audit ledger.
          </p>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Reason / Justification *
            </label>
            <textarea
              required
              rows={3}
              value={actionModal.reason}
              onChange={(e) => setActionModal({ ...actionModal, reason: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              placeholder="e.g. Student requested withdrawal due to medical circumstances..."
            />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={() => setActionModal({ isOpen: false, enrollmentId: null, actionType: null, reason: '' })}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              className={actionModal.actionType === 'cancel' ? 'btn-danger text-xs' : 'btn-primary text-xs'}
            >
              Confirm {actionModal.actionType === 'cancel' ? 'Cancellation' : 'Withdrawal'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

