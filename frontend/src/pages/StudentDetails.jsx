import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { studentsApi } from '../api/students';
import StatusBadge from '../components/common/StatusBadge';
import Modal from '../components/common/Modal';
import {
  ArrowLeft,
  Mail,
  Phone,
  Calendar,
  MapPin,
  Award,
  DollarSign,
  Edit,
  AlertCircle,
  FileSpreadsheet,
} from 'lucide-react';

export default function StudentDetails() {
  const { id } = useParams();
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Edit Modal State
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [editError, setEditError] = useState(null);

  const fetchStudent = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await studentsApi.getStudent(id);
      setStudent(data);
      setEditFormData({
        first_name: data.first_name,
        last_name: data.last_name,
        phone: data.phone || '',
        address: data.address || '',
        city: data.city || '',
        state: data.state || '',
        gpa: data.gpa,
        status: data.status,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load student details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudent();
  }, [id]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setEditError(null);
    try {
      await studentsApi.updateStudent(id, {
        ...editFormData,
        gpa: parseFloat(editFormData.gpa) || 0.0,
      });
      setIsEditOpen(false);
      fetchStudent();
    } catch (err) {
      setEditError(err.response?.data?.detail || 'Failed to update student profile');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-slate-500">Loading student profile...</div>;
  }

  if (error || !student) {
    return (
      <div className="p-8 text-center text-rose-600 bg-white rounded-xl border border-rose-200">
        <AlertCircle className="w-8 h-8 mx-auto mb-2" />
        <p className="font-semibold">{error || 'Student not found'}</p>
        <Link to="/students" className="mt-4 inline-block btn-secondary text-xs">
          &larr; Back to Students
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          to="/students"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Students
        </Link>
        <div className="flex items-center gap-2">
          <Link
            to={`/enrollments?student_id=${student.id}`}
            className="btn-secondary text-xs flex items-center gap-1.5"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            View Enrollments
          </Link>
          <button
            onClick={() => setIsEditOpen(true)}
            className="btn-primary text-xs flex items-center gap-1.5"
          >
            <Edit className="w-3.5 h-3.5" />
            Edit Profile
          </button>
        </div>
      </div>

      {/* Main Student Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">
                {student.first_name} {student.last_name}
              </h1>
              <StatusBadge status={student.status} />
            </div>
            <p className="text-sm font-mono text-slate-500 mt-1">ID: {student.student_id}</p>
          </div>
          <div className="flex sm:flex-col items-center sm:items-end gap-1">
            <span className="text-xs text-slate-400">Cumulative GPA</span>
            <span className="text-2xl font-bold text-primary-700">{student.gpa} / 10.0</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Contact Information
            </h3>
            <div className="flex items-center gap-2.5 text-sm text-slate-700">
              <Mail className="w-4 h-4 text-slate-400 shrink-0" />
              <span>{student.email}</span>
            </div>
            <div className="flex items-center gap-2.5 text-sm text-slate-700">
              <Phone className="w-4 h-4 text-slate-400 shrink-0" />
              <span>{student.phone || 'Not provided'}</span>
            </div>
            <div className="flex items-center gap-2.5 text-sm text-slate-700">
              <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
              <span>DOB: {student.date_of_birth}</span>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Location & Residence
            </h3>
            <div className="flex items-start gap-2.5 text-sm text-slate-700">
              <MapPin className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <p>{student.address || 'Address line not set'}</p>
                <p className="text-slate-500 text-xs mt-0.5">
                  {[student.city, student.state, student.country, student.postal_code]
                    .filter(Boolean)
                    .join(', ')}
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Socio-Economic Profile
            </h3>
            <div className="flex items-center gap-2.5 text-sm text-slate-700">
              <DollarSign className="w-4 h-4 text-slate-400 shrink-0" />
              <span>Income Category: <strong>{student.family_income_category}</strong></span>
            </div>
            <div className="flex items-center gap-2.5 text-sm text-slate-700">
              <Award className="w-4 h-4 text-slate-400 shrink-0" />
              <span>Financial Aid Eligibility: Standard</span>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Student Modal */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title={`Edit Profile: ${student.first_name} ${student.last_name}`}
      >
        {editError && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{editError}</span>
          </div>
        )}

        <form onSubmit={handleUpdate} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                First Name
              </label>
              <input
                type="text"
                required
                value={editFormData.first_name || ''}
                onChange={(e) => setEditFormData({ ...editFormData, first_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Last Name
              </label>
              <input
                type="text"
                required
                value={editFormData.last_name || ''}
                onChange={(e) => setEditFormData({ ...editFormData, last_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Phone
              </label>
              <input
                type="text"
                value={editFormData.phone || ''}
                onChange={(e) => setEditFormData({ ...editFormData, phone: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                GPA (0-10)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="10"
                value={editFormData.gpa || '0.00'}
                onChange={(e) => setEditFormData({ ...editFormData, gpa: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Status
              </label>
              <select
                value={editFormData.status || 'ACTIVE'}
                onChange={(e) => setEditFormData({ ...editFormData, status: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
              >
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
                <option value="GRADUATED">Graduated</option>
                <option value="SUSPENDED">Suspended</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={() => setIsEditOpen(false)}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary text-xs"
            >
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

