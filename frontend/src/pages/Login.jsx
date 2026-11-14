import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock, User, AlertCircle, ArrowRight } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('Admin@2026Secure');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoSelect = (u, p) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
        <div className="text-center">
          <div className="w-12 h-12 bg-primary-600 rounded-xl mx-auto flex items-center justify-center text-white font-bold text-xl shadow-md">
            SF
          </div>
          <h2 className="mt-4 text-2xl font-bold text-slate-900 tracking-tight">
            Sign In to StudentFin
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Student Tuition & Financial Management
          </p>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Username
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                <User className="w-4 h-4" />
              </span>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Username"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Password"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary py-2.5 flex items-center justify-center gap-2 mt-2"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-4 border-t border-slate-200 text-xs text-slate-500 space-y-1">
          <p className="font-semibold text-slate-700 mb-2">Quick Demo Accounts:</p>
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <button
              type="button"
              onClick={() => handleDemoSelect('admin', 'Admin@2026Secure')}
              className="p-1.5 text-left border rounded hover:bg-slate-50 font-medium text-slate-700"
            >
              👑 Platform Admin
            </button>
            <button
              type="button"
              onClick={() => handleDemoSelect('academic_admin', 'Academic@2026Secure')}
              className="p-1.5 text-left border rounded hover:bg-slate-50 font-medium text-slate-700"
            >
              🎓 Academic Admin
            </button>
            <button
              type="button"
              onClick={() => handleDemoSelect('support_staff', 'Support@2026Secure')}
              className="p-1.5 text-left border rounded hover:bg-slate-50 font-medium text-slate-700"
            >
              💼 Support Staff
            </button>
            <button
              type="button"
              onClick={() => handleDemoSelect('learner', 'Student@2026Secure')}
              className="p-1.5 text-left border rounded hover:bg-slate-50 font-medium text-slate-700"
            >
              🎒 Student Learner
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

