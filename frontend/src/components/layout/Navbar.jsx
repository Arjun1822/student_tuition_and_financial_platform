import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { LogOut, User as UserIcon } from 'lucide-react';

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-9 h-9 bg-primary-600 rounded-lg flex items-center justify-center text-white font-bold text-lg shadow-sm">
              SF
            </div>
            <span className="font-bold text-slate-900 text-lg tracking-tight">StudentFin</span>
          </Link>
          <span className="hidden sm:inline-block text-xs font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md border border-slate-200">
            Milestone 3
          </span>
        </div>

        <div className="flex items-center space-x-4">
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="text-xs font-semibold text-slate-600 hover:text-primary-600 transition-colors"
          >
            Swagger Docs
          </a>

          {isAuthenticated ? (
            <div className="flex items-center space-x-3 pl-3 border-l border-slate-200">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-semibold text-xs">
                  {user?.username?.substring(0, 2).toUpperCase() || 'U'}
                </div>
                <div className="hidden md:block text-left">
                  <p className="text-xs font-semibold text-slate-800 leading-none">{user?.username}</p>
                  <p className="text-[10px] font-medium text-slate-500 leading-none mt-1">{user?.role}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="text-slate-400 hover:text-rose-600 p-1 rounded-md hover:bg-slate-100 transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn-primary text-xs py-1.5 px-3">
              Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

