import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { studentsApi } from '../api/students';
import { programsApi } from '../api/programs';
import { enrollmentsApi } from '../api/enrollments';
import { invoicesApi } from '../api/invoices';
import {
  Users,
  GraduationCap,
  FileSpreadsheet,
  Receipt,
  ArrowRight,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState({
    students: 0,
    programs: 0,
    enrollments: 0,
    invoices: 0,
    totalInvoiced: '0.00',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const [stuRes, progRes, enrRes, invRes] = await Promise.all([
          studentsApi.getStudents({ page_size: 1 }),
          programsApi.getPrograms({ page_size: 1 }),
          enrollmentsApi.getEnrollments({ page_size: 1 }),
          invoicesApi.getInvoices({ page_size: 50 }),
        ]);

        const grossTotal = (invRes.items || []).reduce(
          (acc, inv) => acc + parseFloat(inv.gross_amount || 0),
          0
        );

        setStats({
          students: stuRes.total || 0,
          programs: progRes.total || 0,
          enrollments: enrRes.total || 0,
          invoices: invRes.total || 0,
          totalInvoiced: grossTotal.toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }),
        });
      } catch (err) {
        console.error('Failed to load dashboard metrics:', err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  const cards = [
    {
      title: 'Total Students',
      value: stats.students,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      link: '/students',
    },
    {
      title: 'Academic Programs',
      value: stats.programs,
      icon: GraduationCap,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      link: '/programs',
    },
    {
      title: 'Active Enrollments',
      value: stats.enrollments,
      icon: FileSpreadsheet,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      link: '/enrollments',
    },
    {
      title: 'Invoices Issued',
      value: stats.invoices,
      icon: Receipt,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
      link: '/invoices',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-primary-800 to-indigo-900 rounded-2xl p-8 text-white shadow-sm">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-200 mb-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Enterprise Financial Lifecycle Platform
        </div>
        <h1 className="text-3xl font-bold tracking-tight">Financial Control Center</h1>
        <p className="mt-2 text-indigo-100 max-w-2xl text-sm">
          Unified management of students, program fee schedules, term enrollments, and
          automated line-item tuition invoice generation with financial audit trails.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.title}
              className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase">
                    {card.title}
                  </span>
                  <div className={`p-2 rounded-lg ${card.bgColor}`}>
                    <Icon className={`w-5 h-5 ${card.color}`} />
                  </div>
                </div>
                <div className="mt-3">
                  <span className="text-2xl font-bold text-slate-900">
                    {loading ? '...' : card.value}
                  </span>
                </div>
              </div>
              <Link
                to={card.link}
                className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-medium text-primary-600 hover:text-primary-700"
              >
                <span>View All</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          );
        })}
      </div>

      {/* Operational Highlights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-primary-600" />
            Financial Health Summary
          </h2>
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-600">Total Billed Volume:</span>
              <span className="font-bold text-slate-900">₹{stats.totalInvoiced}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-600">Ledger Currency:</span>
              <span className="font-medium text-slate-800">INR (Indian Rupee)</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-600">Financial Storage Precision:</span>
              <span className="font-medium text-slate-800">MySQL DECIMAL(12,2)</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2 mb-4">
            <Receipt className="w-4 h-4 text-primary-600" />
            Quick Actions
          </h2>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <Link
              to="/students"
              className="p-3 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium text-slate-700 flex flex-col justify-between"
            >
              <span>Register Student</span>
              <span className="text-xs text-slate-400 mt-2">&rarr; Form</span>
            </Link>
            <Link
              to="/enrollments"
              className="p-3 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium text-slate-700 flex flex-col justify-between"
            >
              <span>Enroll in Program</span>
              <span className="text-xs text-slate-400 mt-2">&rarr; Form</span>
            </Link>
            <Link
              to="/invoices"
              className="p-3 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium text-slate-700 flex flex-col justify-between"
            >
              <span>Generate Invoice</span>
              <span className="text-xs text-slate-400 mt-2">&rarr; Service</span>
            </Link>
            <Link
              to="/fee-schedules"
              className="p-3 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium text-slate-700 flex flex-col justify-between"
            >
              <span>Fee Schedules</span>
              <span className="text-xs text-slate-400 mt-2">&rarr; View 80 schedules</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

