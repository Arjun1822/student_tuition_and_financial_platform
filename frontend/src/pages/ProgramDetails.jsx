import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { programsApi } from '../api/programs';
import { feeSchedulesApi } from '../api/feeSchedules';
import StatusBadge from '../components/common/StatusBadge';
import Modal from '../components/common/Modal';
import {
  ArrowLeft,
  BookOpen,
  Building,
  GraduationCap,
  Clock,
  Award,
  Edit,
  AlertCircle,
  FileSpreadsheet,
} from 'lucide-react';

export default function ProgramDetails() {
  const { id } = useParams();
  const [program, setProgram] = useState(null);
  const [feeSchedules, setFeeSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Edit Modal State
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [editError, setEditError] = useState(null);

  const fetchProgramData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await programsApi.getProgram(id);
      setProgram(data);
      setEditFormData({
        name: data.name,
        department: data.department,
        degree_level: data.degree_level,
        duration_years: data.duration_years,
        total_credits: data.total_credits,
        status: data.status,
        description: data.description || '',
      });

      // Fetch related fee schedules
      try {
        const feesData = await feeSchedulesApi.getFeeSchedules({ program_id: data.id });
        setFeeSchedules(feesData.items || []);
      } catch (fErr) {
        // Soft fail on secondary relationship
        setFeeSchedules([]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load program details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProgramData();
  }, [id]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setEditError(null);
    try {
      await programsApi.updateProgram(id, {
        ...editFormData,
        duration_years: parseInt(editFormData.duration_years, 10),
        total_credits: parseInt(editFormData.total_credits, 10),
      });
      setIsEditOpen(false);
      fetchProgramData();
    } catch (err) {
      setEditError(err.response?.data?.detail || 'Failed to update academic program');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-slate-500">Loading program details...</div>;
  }

  if (error || !program) {
    return (
      <div className="p-8 text-center text-rose-600 bg-white rounded-xl border border-rose-200">
        <AlertCircle className="w-8 h-8 mx-auto mb-2" />
        <p className="font-semibold">{error || 'Academic program not found'}</p>
        <Link to="/programs" className="mt-4 inline-block btn-secondary text-xs">
          &larr; Back to Programs
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          to="/programs"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Programs
        </Link>
        <button
          onClick={() => setIsEditOpen(true)}
          className="btn-secondary flex items-center gap-1.5 text-xs"
        >
          <Edit className="w-3.5 h-3.5" />
          Edit Program
        </button>
      </div>

      {/* Main Program Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-slate-100 gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-indigo-50 border border-indigo-100 rounded-xl flex items-center justify-center text-indigo-600 font-bold text-xl shadow-xs">
              <BookOpen className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-slate-900">{program.name}</h1>
                <StatusBadge status={program.status} />
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Code: <span className="font-mono font-medium text-slate-700">{program.code}</span> | ID:{' '}
                <span className="font-mono font-medium text-slate-700">{program.program_id}</span>
              </p>
            </div>
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 pt-6">
          <div className="flex items-start gap-3">
            <Building className="w-5 h-5 text-slate-400 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-slate-400">Department</p>
              <p className="text-sm font-semibold text-slate-800 mt-0.5">{program.department}</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <GraduationCap className="w-5 h-5 text-slate-400 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-slate-400">Degree Level</p>
              <p className="text-sm font-semibold text-slate-800 mt-0.5">{program.degree_level}</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Clock className="w-5 h-5 text-slate-400 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-slate-400">Duration</p>
              <p className="text-sm font-semibold text-slate-800 mt-0.5">{program.duration_years} Years</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Award className="w-5 h-5 text-slate-400 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-slate-400">Total Credits</p>
              <p className="text-sm font-semibold text-slate-800 mt-0.5">{program.total_credits} Credits</p>
            </div>
          </div>
        </div>

        {program.description && (
          <div className="mt-6 pt-6 border-t border-slate-100">
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Program Overview</h2>
            <p className="text-sm text-slate-600 leading-relaxed">{program.description}</p>
          </div>
        )}
      </div>

      {/* Associated Fee Schedules */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-primary-600" />
            <h2 className="text-sm font-semibold text-slate-900">Program Fee Schedules</h2>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            {feeSchedules.length} {feeSchedules.length === 1 ? 'Schedule' : 'Schedules'} configured
          </span>
        </div>

        {feeSchedules.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No fee schedules configured for this program.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Schedule ID</th>
                  <th className="px-6 py-3">Term</th>
                  <th className="px-6 py-3">Tuition Fee</th>
                  <th className="px-6 py-3">Total Fee</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {feeSchedules.map((fee) => (
                  <tr key={fee.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-3.5 font-mono font-medium text-slate-900">{fee.fee_schedule_id}</td>
                    <td className="px-6 py-3.5 font-medium">{fee.term?.name || `Term #${fee.term_id}`}</td>
                    <td className="px-6 py-3.5">INR {parseFloat(fee.tuition_fee || 0).toLocaleString()}</td>
                    <td className="px-6 py-3.5 font-semibold text-slate-900">
                      INR {parseFloat(fee.total_fee || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-3.5">
                      <StatusBadge status={fee.is_active ? 'ACTIVE' : 'INACTIVE'} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit Program Modal */}
      <Modal isOpen={isEditOpen} onClose={() => setIsEditOpen(false)} title="Edit Program Details">
        <form onSubmit={handleUpdate} className="space-y-4">
          {editError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{editError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Program Name</label>
            <input
              type="text"
              required
              className="input-field"
              value={editFormData.name || ''}
              onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Department</label>
              <input
                type="text"
                required
                className="input-field"
                value={editFormData.department || ''}
                onChange={(e) => setEditFormData({ ...editFormData, department: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Degree Level</label>
              <select
                className="input-field"
                value={editFormData.degree_level || 'BACHELOR'}
                onChange={(e) => setEditFormData({ ...editFormData, degree_level: e.target.value })}
              >
                <option value="CERTIFICATE">Certificate</option>
                <option value="DIPLOMA">Diploma</option>
                <option value="BACHELOR">Bachelor</option>
                <option value="MASTER">Master</option>
                <option value="DOCTORATE">Doctorate</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Duration (Years)</label>
              <input
                type="number"
                min="1"
                max="8"
                required
                className="input-field"
                value={editFormData.duration_years || 4}
                onChange={(e) => setEditFormData({ ...editFormData, duration_years: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Total Credits</label>
              <input
                type="number"
                min="1"
                required
                className="input-field"
                value={editFormData.total_credits || 120}
                onChange={(e) => setEditFormData({ ...editFormData, total_credits: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Status</label>
              <select
                className="input-field"
                value={editFormData.status || 'ACTIVE'}
                onChange={(e) => setEditFormData({ ...editFormData, status: e.target.value })}
              >
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
                <option value="ARCHIVED">Archived</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
            <textarea
              rows={3}
              className="input-field"
              value={editFormData.description || ''}
              onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsEditOpen(false)}
              className="btn-secondary text-xs"
              disabled={submitting}
            >
              Cancel
            </button>
            <button type="submit" className="btn-primary text-xs" disabled={submitting}>
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
