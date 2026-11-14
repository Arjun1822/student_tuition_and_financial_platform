import React from 'react';

const STATUS_STYLES = {
  ACTIVE: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  COMPLETED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  PAID: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  ISSUED: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  PARTIALLY_PAID: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  PENDING: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  OVERDUE: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  CANCELLED: 'bg-slate-100 text-slate-700 ring-slate-500/20',
  WITHDRAWN: 'bg-purple-50 text-purple-700 ring-purple-600/20',
  SUSPENDED: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  INACTIVE: 'bg-slate-100 text-slate-700 ring-slate-500/20',
};

export default function StatusBadge({ status }) {
  const normalized = status ? status.toUpperCase() : 'UNKNOWN';
  const style = STATUS_STYLES[normalized] || 'bg-slate-100 text-slate-700 ring-slate-500/20';

  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${style}`}
    >
      {status || 'Unknown'}
    </span>
  );
}

