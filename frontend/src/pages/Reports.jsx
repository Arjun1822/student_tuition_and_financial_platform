import React, { useState, useEffect } from 'react';
import { reportsApi } from '../api/reports';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  BarChart3,
  RefreshCw,
  TrendingUp,
  CreditCard,
  AlertCircle,
  Award,
  Users,
  Receipt,
  FileSpreadsheet,
} from 'lucide-react';

const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#64748b'];

export default function Reports() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRefreshed, setLastRefreshed] = useState(new Date());

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await reportsApi.getDashboardMetrics();
      setData(resp);
      setLastRefreshed(new Date());
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch financial reports');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const formatCurrency = (val) => {
    const num = parseFloat(val) || 0;
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  };

  const kpis = data?.kpis || {};
  const charts = data?.charts || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Executive Financial Analytics</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time receivables, revenue realization, institutional aid utilization, and exception analytics.
          </p>
        </div>
        <button
          onClick={fetchReports}
          disabled={loading}
          className="btn-secondary flex items-center gap-2 self-start sm:self-auto text-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Data ({lastRefreshed.toLocaleTimeString()})
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-600 font-bold hover:underline">Dismiss</button>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Gross Invoiced</p>
            <p className="text-2xl font-bold text-slate-900 font-mono mt-1">
              {loading ? '—' : formatCurrency(kpis.total_invoice_value)}
            </p>
            <p className="text-xs text-slate-400 mt-0.5">{kpis.active_enrollments || 0} active enrollments</p>
          </div>
          <div className="w-11 h-11 bg-primary-50 text-primary-600 rounded-xl flex items-center justify-center">
            <Receipt className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Payments Collected</p>
            <p className="text-2xl font-bold text-emerald-600 font-mono mt-1">
              {loading ? '—' : formatCurrency(kpis.payments_collected)}
            </p>
            <p className="text-xs text-emerald-600 mt-0.5 font-medium">Realized revenue</p>
          </div>
          <div className="w-11 h-11 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center">
            <CreditCard className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Outstanding Balance</p>
            <p className="text-2xl font-bold text-rose-600 font-mono mt-1">
              {loading ? '—' : formatCurrency(kpis.outstanding_balance)}
            </p>
            <p className="text-xs text-rose-500 mt-0.5 font-medium">{kpis.overdue_invoices || 0} overdue invoices</p>
          </div>
          <div className="w-11 h-11 bg-rose-50 text-rose-600 rounded-xl flex items-center justify-center">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Scholarships Awarded</p>
            <p className="text-2xl font-bold text-purple-600 font-mono mt-1">
              {loading ? '—' : formatCurrency(kpis.scholarships_awarded)}
            </p>
            <p className="text-xs text-purple-600 mt-0.5 font-medium">Fee waivers & grants</p>
          </div>
          <div className="w-11 h-11 bg-purple-50 text-purple-600 rounded-xl flex items-center justify-center">
            <Award className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Secondary Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
        <div>
          <span className="text-slate-500 block">Total Students:</span>
          <span className="font-bold text-slate-800 text-sm">{kpis.total_students || 0}</span>
        </div>
        <div>
          <span className="text-slate-500 block">Refunds Processed:</span>
          <span className="font-bold text-slate-800 text-sm font-mono">{formatCurrency(kpis.refunds_processed)}</span>
        </div>
        <div>
          <span className="text-slate-500 block">Late Fees Assessed:</span>
          <span className="font-bold text-amber-700 text-sm font-mono">{formatCurrency(kpis.late_fees_assessed)}</span>
        </div>
        <div>
          <span className="text-slate-500 block">Unresolved Anomalies:</span>
          <span className="font-bold text-rose-600 text-sm">{kpis.unresolved_anomalies || 0}</span>
        </div>
      </div>

      {/* Recharts Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Outstanding by Academic Program */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Outstanding Balance by Academic Program</h3>
            <p className="text-xs text-slate-500">Top programs with largest receivable liabilities</p>
          </div>
          <div className="h-72 w-full">
            {charts.outstanding_by_program && charts.outstanding_by_program.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.outstanding_by_program} margin={{ top: 10, right: 20, left: 20, bottom: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="program" tick={{ fontSize: 11, fill: '#64748b' }} angle={-25} textAnchor="end" />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickFormatter={(val) => `₹${val / 1000}k`} />
                  <Tooltip
                    formatter={(val) => [formatCurrency(val), 'Outstanding']}
                    contentStyle={{ borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Bar dataKey="outstanding" fill="#2563eb" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No program receivable data available
              </div>
            )}
          </div>
        </div>

        {/* Chart 2: Invoices by Billing Status */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Invoice Portfolio by Status</h3>
            <p className="text-xs text-slate-500">Distribution of invoices across lifecycle stages</p>
          </div>
          <div className="h-72 w-full">
            {charts.invoices_by_status && charts.invoices_by_status.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={charts.invoices_by_status}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={95}
                    innerRadius={45}
                    paddingAngle={3}
                    label={({ status, count }) => `${status}: ${count}`}
                  >
                    {charts.invoices_by_status.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val, name) => [val, `Count`]}
                    contentStyle={{ borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No invoice status distribution available
              </div>
            )}
          </div>
        </div>

        {/* Chart 3: Payments by Settlement Status */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Payments by Settlement Status</h3>
            <p className="text-xs text-slate-500">Volume breakdown of payment processing states</p>
          </div>
          <div className="h-72 w-full">
            {charts.payments_by_status && charts.payments_by_status.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.payments_by_status} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="status" tick={{ fontSize: 11, fill: '#64748b' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                  <Tooltip
                    formatter={(val) => [val, 'Count']}
                    contentStyle={{ borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No payment status distribution available
              </div>
            )}
          </div>
        </div>

        {/* Chart 4: Detected Anomalies by Heuristic Type */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Detected Exceptions by Anomaly Type</h3>
            <p className="text-xs text-slate-500">Audit classification of identified financial anomalies</p>
          </div>
          <div className="h-72 w-full">
            {charts.anomalies_by_type && charts.anomalies_by_type.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={charts.anomalies_by_type}
                    dataKey="count"
                    nameKey="issue_type"
                    cx="50%"
                    cy="50%"
                    outerRadius={95}
                    paddingAngle={4}
                    label={({ issue_type, count }) => `${issue_type}: ${count}`}
                  >
                    {charts.anomalies_by_type.map((entry, index) => (
                      <Cell key={`cell-anm-${index}`} fill={COLORS[(index + 3) % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val) => [val, 'Detected Anomalies']}
                    contentStyle={{ borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No anomaly classification records available
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
