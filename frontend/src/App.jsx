import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { authApi } from './api/auth';
import { Activity, ShieldCheck, Database, Layers, CheckCircle2 } from 'lucide-react';

function HealthOverview() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    authApi.checkHealth()
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to connect to API');
        setLoading(false);
      });
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mb-8">
        <div className="bg-gradient-to-r from-primary-700 to-indigo-800 px-8 py-10 text-white">
          <div className="flex items-center space-x-3 mb-2">
            <span className="px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-xs font-semibold uppercase tracking-wider">
              Milestone 1 Verified
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Student Financial Platform</h1>
          <p className="mt-2 text-indigo-100 max-w-3xl">
            Tuition, Scholarship, Payment & Financial Reconciliation Management Platform.
            Three-tier production architecture: React + FastAPI + MySQL 8.
          </p>
        </div>

        <div className="p-8">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary-600" />
            System Architecture Status
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Presentation Tier */}
            <div className="p-5 rounded-xl border border-slate-200 bg-slate-50/50">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500 uppercase">Tier 1: Presentation</span>
                <span className="flex items-center text-xs font-medium text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Active
                </span>
              </div>
              <p className="font-semibold text-slate-800">React 18 + Vite</p>
              <p className="text-xs text-slate-500 mt-1">Tailwind CSS, React Router, Axios, Lucide Icons</p>
            </div>

            {/* Application Tier */}
            <div className="p-5 rounded-xl border border-slate-200 bg-slate-50/50">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500 uppercase">Tier 2: Application</span>
                {loading ? (
                  <span className="text-xs font-medium text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">Probing...</span>
                ) : health ? (
                  <span className="flex items-center text-xs font-medium text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Healthy
                  </span>
                ) : (
                  <span className="text-xs font-medium text-rose-700 bg-rose-100 px-2 py-0.5 rounded-full">Offline</span>
                )}
              </div>
              <p className="font-semibold text-slate-800">FastAPI (Python 3.12)</p>
              <p className="text-xs text-slate-500 mt-1">
                {health ? `Version: ${health.version} | ${health.service}` : (error || 'Waiting for API backend...')}
              </p>
            </div>

            {/* Data Tier */}
            <div className="p-5 rounded-xl border border-slate-200 bg-slate-50/50">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500 uppercase">Tier 3: Database</span>
                <span className="flex items-center text-xs font-medium text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                  <Database className="w-3.5 h-3.5 mr-1" /> MySQL 8.0 InnoDB
                </span>
              </div>
              <p className="font-semibold text-slate-800">SQLAlchemy 2.0 + PyMySQL</p>
              <p className="text-xs text-slate-500 mt-1">Decimal precision, transactions, foreign key constraints</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-slate-50">
        <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 bg-primary-600 rounded-lg flex items-center justify-center text-white font-bold text-lg shadow-sm">
                SF
              </div>
              <span className="font-bold text-slate-900 text-lg tracking-tight">StudentFin</span>
              <span className="ml-2 text-xs font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md border border-slate-200">
                v1.0.0
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <a
                href="/docs"
                target="_blank"
                rel="noreferrer"
                className="text-xs font-semibold text-slate-600 hover:text-primary-600 transition-colors"
              >
                Swagger API Docs &rarr;
              </a>
            </div>
          </div>
        </header>

        <main>
          <HealthOverview />
        </main>
      </div>
    </AuthProvider>
  );
}
