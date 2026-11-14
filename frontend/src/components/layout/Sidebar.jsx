import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  CalendarDays,
  FileSpreadsheet,
  Receipt,
  Award,
  CreditCard,
  RotateCcw,
  BookOpen,
  Scale,
  AlertTriangle,
  BarChart3,
} from 'lucide-react';

const ACADEMIC_ITEMS = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Students', path: '/students', icon: Users },
  { name: 'Programs', path: '/programs', icon: GraduationCap },
  { name: 'Fee Schedules', path: '/fee-schedules', icon: CalendarDays },
  { name: 'Enrollments', path: '/enrollments', icon: FileSpreadsheet },
  { name: 'Invoices', path: '/invoices', icon: Receipt },
];

const FINANCIAL_ITEMS = [
  { name: 'Scholarships', path: '/scholarships', icon: Award },
  { name: 'Payments', path: '/payments', icon: CreditCard },
  { name: 'Refunds', path: '/refunds', icon: RotateCcw },
  { name: 'Ledger & Audit', path: '/ledger', icon: BookOpen },
  { name: 'Reconciliation', path: '/reconciliation', icon: Scale },
  { name: 'Anomalies', path: '/anomalies', icon: AlertTriangle },
  { name: 'Financial Reports', path: '/reports', icon: BarChart3 },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 min-h-[calc(100vh-4rem)] p-4 flex flex-col justify-between shrink-0">
      <div className="space-y-6">
        <nav className="space-y-1">
          <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Academic Operations
          </p>
          {ACADEMIC_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700 font-semibold'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        <nav className="space-y-1">
          <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Financial Management
          </p>
          {FINANCIAL_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700 font-semibold'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-500 mt-6">
        <p className="font-semibold text-slate-700">Financial Platform</p>
        <p className="mt-0.5 text-[11px]">Strict 3-Tier Architecture</p>
        <div className="mt-2 flex items-center gap-1.5 text-emerald-700 font-medium text-[11px]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          MySQL 8.0 Live
        </div>
      </div>
    </aside>
  );
}
