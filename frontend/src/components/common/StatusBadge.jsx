import React from 'react';

const STATUS_STYLES = {
  ACTIVE: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  COMPLETED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  PAID: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  APPROVED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  PROCESSED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  MATCHED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  RESOLVED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  
  ISSUED: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  OPEN: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  LOW: 'bg-blue-50 text-blue-700 ring-blue-600/20',

  PARTIALLY_PAID: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  PENDING: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  EXCEPTION: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  UNRESOLVED: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  MEDIUM: 'bg-amber-50 text-amber-700 ring-amber-600/20',

  OVERDUE: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  SUSPENDED: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  REJECTED: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  REVERSED: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  FAILED: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  MISMATCHED: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  CRITICAL: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  HIGH: 'bg-rose-50 text-rose-700 ring-rose-600/20',

  REFUNDED: 'bg-purple-50 text-purple-700 ring-purple-600/20',
  WITHDRAWN: 'bg-purple-50 text-purple-700 ring-purple-600/20',
  EXHAUSTED: 'bg-purple-50 text-purple-700 ring-purple-600/20',

  CANCELLED: 'bg-slate-100 text-slate-700 ring-slate-500/20',
  INACTIVE: 'bg-slate-100 text-slate-700 ring-slate-500/20',
  EXPIRED: 'bg-slate-100 text-slate-700 ring-slate-500/20',
};

export default function StatusBadge({ status }) {
  const normalized = status ? status.toUpperCase() : 'UNKNOWN';
  const style = STATUS_STYLES[normalized] || 'bg-slate-100 text-slate-700 ring-slate-500/20';

  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${style}`}
    >
      {status || 'Unknown'}
    </span>
  );
}
