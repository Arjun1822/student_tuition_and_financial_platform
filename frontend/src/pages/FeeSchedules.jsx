import React, { useState, useEffect } from 'react';
import { feeSchedulesApi } from '../api/feeSchedules';
import { programsApi } from '../api/programs';
import StatusBadge from '../components/common/StatusBadge';
import Pagination from '../components/common/Pagination';
import Modal from '../components/common/Modal';
import { CalendarDays, Plus, AlertCircle } from 'lucide-react';

export default function FeeSchedules() {
  const [schedules, setSchedules] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [programsList, setProgramsList] = useState([]);
  const [selectedProgram, setSelectedProgram] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [formData, setFormData] = useState({
    program_id: '',
    term_id: 1,
    tuition_fee: '75000.00',
    registration_fee: '5000.00',
    laboratory_fee: '10000.00',
    examination_fee: '4000.00',
    library_fee: '3000.00',
    other_charges: '2000.00',
    currency: 'INR',
    effective_start_date: '2026-01-12',
    effective_end_date: '2026-05-20',
    is_active: true,
  });

  const fetchSchedules = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await feeSchedulesApi.getFeeSchedules({
        page,
        page_size: 15,
        program_id: selectedProgram ? parseInt(selectedProgram, 10) : undefined,
      });
      setSchedules(data.items);
      setTotal(data.total);
      setPages(data.pages);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load fee schedules');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load programs for dropdown
    programsApi.getPrograms({ page_size: 100 })
      .then((data) => setProgramsList(data.items || []))
      .catch((e) => console.error(e));
  }, []);

  useEffect(() => {
    fetchSchedules();
  }, [page, selectedProgram]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      await feeSchedulesApi.createFeeSchedule({
        ...formData,
        program_id: parseInt(formData.program_id, 10),
        term_id: parseInt(formData.term_id, 10),
        tuition_fee: formData.tuition_fee,
        registration_fee: formData.registration_fee,
        laboratory_fee: formData.laboratory_fee,
        examination_fee: formData.examination_fee,
        library_fee: formData.library_fee,
        other_charges: formData.other_charges,
      });
      setIsModalOpen(false);
      fetchSchedules();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to configure fee schedule');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Fee Schedules</h1>
          <p className="text-sm text-slate-500 mt-1">
            Program- and term-specific fee structures with verified line-item totals.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Configure Schedule
        </button>
      </div>

      {/* Program Filter */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
        <label className="text-xs font-semibold text-slate-600 uppercase">Filter Program:</label>
        <select
          value={selectedProgram}
          onChange={(e) => {
            setSelectedProgram(e.target.value);
            setPage(1);
          }}
          className="border border-slate-300 rounded-lg text-sm px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 max-w-md"
        >
          <option value="">All Programs ({programsList.length})</option>
          {programsList.map((p) => (
            <option key={p.id} value={p.id}>
              {p.code} - {p.name}
            </option>
          ))}
        </select>
      </div>

      {/* Schedules Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">Loading fee schedules...</div>
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
                  <th className="px-6 py-3.5">Schedule ID</th>
                  <th className="px-6 py-3.5">Program</th>
                  <th className="px-6 py-3.5">Academic Term</th>
                  <th className="px-6 py-3.5">Tuition</th>
                  <th className="px-6 py-3.5">Lab / Amenities</th>
                  <th className="px-6 py-3.5 font-bold text-slate-900">Total Collectible</th>
                  <th className="px-6 py-3.5">Effective Dates</th>
                  <th className="px-6 py-3.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {schedules.map((fs) => (
                  <tr key={fs.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-slate-900">
                      {fs.fee_schedule_id}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-slate-900">{fs.program?.code}</span>
                      <p className="text-xs text-slate-500">{fs.program?.name}</p>
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-800">
                      {fs.term?.name || fs.term?.term_id}
                    </td>
                    <td className="px-6 py-4 font-mono font-medium text-slate-800">
                      ₹{parseFloat(fs.tuition_fee).toLocaleString('en-IN')}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-600">
                      ₹{parseFloat(fs.laboratory_fee).toLocaleString('en-IN')}
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-primary-700">
                      ₹{parseFloat(fs.total_fee).toLocaleString('en-IN')}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500">
                      {fs.effective_start_date} &rarr; {fs.effective_end_date}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={fs.is_active ? 'ACTIVE' : 'INACTIVE'} />
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

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Configure Program Fee Schedule"
      >
        {formError && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{formError}</span>
          </div>
        )}

        <form onSubmit={handleCreate} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Program *
              </label>
              <select
                required
                value={formData.program_id}
                onChange={(e) => setFormData({ ...formData, program_id: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
              >
                <option value="">Select Program</option>
                {programsList.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.code} - {p.name}
                  </option>
                ))}
              </select>
            </div>
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
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Tuition Fee (₹) *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.tuition_fee}
                onChange={(e) => setFormData({ ...formData, tuition_fee: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Registration Fee (₹)
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.registration_fee}
                onChange={(e) => setFormData({ ...formData, registration_fee: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Laboratory Fee (₹)
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.laboratory_fee}
                onChange={(e) => setFormData({ ...formData, laboratory_fee: e.target.value })}
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
              {submitting ? 'Saving...' : 'Save Schedule'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

