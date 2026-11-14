import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { programsApi } from '../api/programs';
import StatusBadge from '../components/common/StatusBadge';
import Pagination from '../components/common/Pagination';
import Modal from '../components/common/Modal';
import { GraduationCap, Plus, Search, Eye, AlertCircle } from 'lucide-react';

export default function Programs() {
  const [programs, setPrograms] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [department, setDepartment] = useState('');
  const [degreeLevel, setDegreeLevel] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    department: '',
    degree_level: 'BACHELOR',
    duration_years: 4,
    total_credits: 160,
    status: 'ACTIVE',
    description: '',
  });

  const fetchPrograms = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await programsApi.getPrograms({
        page,
        page_size: 15,
        department: department || undefined,
        degree_level: degreeLevel || undefined,
      });
      setPrograms(data.items);
      setTotal(data.total);
      setPages(data.pages);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load programs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrograms();
  }, [page, department, degreeLevel]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      await programsApi.createProgram({
        ...formData,
        duration_years: parseInt(formData.duration_years, 10),
        total_credits: parseInt(formData.total_credits, 10),
      });
      setIsModalOpen(false);
      setFormData({
        name: '',
        code: '',
        department: '',
        degree_level: 'BACHELOR',
        duration_years: 4,
        total_credits: 160,
        status: 'ACTIVE',
        description: '',
      });
      fetchPrograms();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create program');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Academic Programs</h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse all institutional degree programs and curriculum specifications.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Add Program
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3">
        <select
          value={department}
          onChange={(e) => {
            setDepartment(e.target.value);
            setPage(1);
          }}
          className="border border-slate-300 rounded-lg text-sm px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Departments</option>
          <option value="School of Computing">School of Computing</option>
          <option value="School of Electrical">School of Electrical</option>
          <option value="School of Mechanical">School of Mechanical</option>
          <option value="School of Civil">School of Civil</option>
          <option value="School of BioSciences">School of BioSciences</option>
          <option value="School of Management">School of Management</option>
          <option value="School of Continuing Education">School of Continuing Education</option>
        </select>

        <select
          value={degreeLevel}
          onChange={(e) => {
            setDegreeLevel(e.target.value);
            setPage(1);
          }}
          className="border border-slate-300 rounded-lg text-sm px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Degree Levels</option>
          <option value="BACHELOR">Bachelor</option>
          <option value="MASTER">Master</option>
          <option value="DOCTORATE">Doctorate</option>
          <option value="DIPLOMA">Diploma</option>
        </select>
      </div>

      {/* Programs Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">Loading programs...</div>
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
                  <th className="px-6 py-3.5">Program ID</th>
                  <th className="px-6 py-3.5">Code</th>
                  <th className="px-6 py-3.5">Program Name</th>
                  <th className="px-6 py-3.5">Department</th>
                  <th className="px-6 py-3.5">Level</th>
                  <th className="px-6 py-3.5">Duration</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {programs.map((prog) => (
                  <tr key={prog.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-slate-900">
                      {prog.program_id}
                    </td>
                    <td className="px-6 py-4 font-mono font-semibold text-primary-700">
                      {prog.code}
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-900">{prog.name}</td>
                    <td className="px-6 py-4 text-slate-600">{prog.department}</td>
                    <td className="px-6 py-4 text-xs font-semibold text-slate-700">
                      {prog.degree_level}
                    </td>
                    <td className="px-6 py-4 text-slate-600">{prog.duration_years} Years ({prog.total_credits} cr)</td>
                    <td className="px-6 py-4">
                      <StatusBadge status={prog.status} />
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/programs/${prog.id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-primary-600 hover:text-primary-700"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Details
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

      {/* Add Program Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add New Academic Program"
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
              Program Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              placeholder="e.g. Master of Science in Data Analytics"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Program Code *
              </label>
              <input
                type="text"
                required
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm uppercase"
                placeholder="e.g. MS-DATA"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Department *
              </label>
              <input
                type="text"
                required
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                placeholder="e.g. School of Computing"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Degree Level
              </label>
              <select
                value={formData.degree_level}
                onChange={(e) => setFormData({ ...formData, degree_level: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
              >
                <option value="BACHELOR">Bachelor</option>
                <option value="MASTER">Master</option>
                <option value="DOCTORATE">Doctorate</option>
                <option value="DIPLOMA">Diploma</option>
                <option value="CERTIFICATE">Certificate</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Duration (Years)
              </label>
              <input
                type="number"
                min="1"
                max="8"
                required
                value={formData.duration_years}
                onChange={(e) => setFormData({ ...formData, duration_years: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Total Credits
              </label>
              <input
                type="number"
                min="10"
                max="300"
                required
                value={formData.total_credits}
                onChange={(e) => setFormData({ ...formData, total_credits: e.target.value })}
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
              {submitting ? 'Creating...' : 'Create Program'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

