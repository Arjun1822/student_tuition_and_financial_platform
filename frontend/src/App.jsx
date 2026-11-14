import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/layout/Navbar';
import Sidebar from './components/layout/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Students from './pages/Students';
import StudentDetails from './pages/StudentDetails';
import Programs from './pages/Programs';
import ProgramDetails from './pages/ProgramDetails';
import FeeSchedules from './pages/FeeSchedules';
import Enrollments from './pages/Enrollments';
import EnrollmentDetails from './pages/EnrollmentDetails';
import Invoices from './pages/Invoices';
import InvoiceDetails from './pages/InvoiceDetails';
import Scholarships from './pages/Scholarships';
import Payments from './pages/Payments';
import Refunds from './pages/Refunds';
import Ledger from './pages/Ledger';
import Reconciliation from './pages/Reconciliation';
import Anomalies from './pages/Anomalies';
import Reports from './pages/Reports';

function ProtectedLayout() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-sm">
        Authenticating session...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected Application Routes */}
          <Route element={<ProtectedLayout />}>
            <Route path="/" element={<Dashboard />} />
            
            {/* Student Lifecycle */}
            <Route path="/students" element={<Students />} />
            <Route path="/students/:id" element={<StudentDetails />} />

            {/* Academic Structure */}
            <Route path="/programs" element={<Programs />} />
            <Route path="/programs/:id" element={<ProgramDetails />} />
            <Route path="/fee-schedules" element={<FeeSchedules />} />

            {/* Enrollments & Invoices */}
            <Route path="/enrollments" element={<Enrollments />} />
            <Route path="/enrollments/:id" element={<EnrollmentDetails />} />
            <Route path="/invoices" element={<Invoices />} />
            <Route path="/invoices/:id" element={<InvoiceDetails />} />

            {/* Financial Management Core (Task 4) */}
            <Route path="/scholarships" element={<Scholarships />} />
            <Route path="/payments" element={<Payments />} />
            <Route path="/refunds" element={<Refunds />} />
            <Route path="/ledger" element={<Ledger />} />
            <Route path="/reconciliation" element={<Reconciliation />} />
            <Route path="/anomalies" element={<Anomalies />} />
            <Route path="/reports" element={<Reports />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
