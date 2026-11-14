import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

import Scholarships from '../pages/Scholarships';
import Payments from '../pages/Payments';
import Refunds from '../pages/Refunds';
import Ledger from '../pages/Ledger';
import Reconciliation from '../pages/Reconciliation';
import Anomalies from '../pages/Anomalies';
import Reports from '../pages/Reports';

import { scholarshipsApi } from '../api/scholarships';
import { paymentsApi } from '../api/payments';
import { refundsApi } from '../api/refunds';
import { ledgerApi } from '../api/ledger';
import { reconciliationApi } from '../api/reconciliation';
import { anomaliesApi } from '../api/anomalies';
import { reportsApi } from '../api/reports';

// Mock Recharts ResponsiveContainer to render children directly in jsdom
vi.mock('recharts', async () => {
  const original = await vi.importActual('recharts');
  return {
    ...original,
    ResponsiveContainer: ({ children }) => (
      <div className="recharts-responsive-container" style={{ width: 400, height: 300 }}>
        {children}
      </div>
    ),
  };
});

// Mock API modules
vi.mock('../api/scholarships');
vi.mock('../api/payments');
vi.mock('../api/refunds');
vi.mock('../api/ledger');
vi.mock('../api/reconciliation');
vi.mock('../api/anomalies');
vi.mock('../api/reports');

describe('Task 4: Financial Management Frontend Pages', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1. SCHOLARSHIPS
  describe('Scholarships Page', () => {
    it('renders scholarship schemes and switches tabs to awards', async () => {
      scholarshipsApi.getScholarships.mockResolvedValue({
        items: [
          {
            id: 1,
            scholarship_id: 'SCH-2026-000001',
            name: 'Merit Excellence Award',
            scholarship_type: 'MERIT',
            percentage: '50.00',
            max_amount: '100000.00',
            total_budget: '1000000.00',
            awarded_amount: '250000.00',
            remaining_budget: '750000.00',
            status: 'ACTIVE',
            academic_year: '2026-2027',
          },
        ],
        total: 1,
        page: 1,
        pages: 1,
      });

      scholarshipsApi.getEligibilities.mockResolvedValue({
        items: [
          {
            id: 101,
            eligibility_id: 'ELG-2026-000001',
            student_id: 1,
            student_name: 'John Doe',
            student_business_id: 'STU-000001',
            scholarship_name: 'Merit Excellence Award',
            scholarship_percentage: '50.00',
            calculated_amount: '50000.00',
            approved_amount: '50000.00',
            status: 'PENDING',
          },
        ],
        total: 1,
        page: 1,
        pages: 1,
      });

      render(
        <MemoryRouter>
          <Scholarships />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Scholarships & Grants')).toBeInTheDocument();
        expect(screen.getByText('Merit Excellence Award')).toBeInTheDocument();
        expect(screen.getByText('SCH-2026-000001')).toBeInTheDocument();
      });

      // Switch to Awards tab
      const awardsTab = screen.getByText(/Award Approvals & Applications/i);
      fireEvent.click(awardsTab);

      await waitFor(() => {
        expect(screen.getByText('ELG-2026-000001')).toBeInTheDocument();
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
    });
  });

  // 2. PAYMENTS
  describe('Payments Page', () => {
    it('renders payments table with allocations and record modal triggers', async () => {
      paymentsApi.getPayments.mockResolvedValue({
        items: [
          {
            id: 1,
            payment_id: 'PAY-2026-000001',
            student_id: 1,
            student_name: 'Alice Smith',
            student_business_id: 'STU-000002',
            amount: '60000.00',
            allocated_amount: '60000.00',
            unallocated_amount: '0.00',
            payment_method: 'BANK_TRANSFER',
            reference_number: 'UTR-999888',
            status: 'COMPLETED',
          },
        ],
        total: 1,
        page: 1,
        pages: 1,
      });

      render(
        <MemoryRouter>
          <Payments />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Payments & Receipts')).toBeInTheDocument();
        expect(screen.getByText('PAY-2026-000001')).toBeInTheDocument();
        expect(screen.getByText('Alice Smith')).toBeInTheDocument();
        expect(screen.getByText('UTR-999888')).toBeInTheDocument();
      });

      // Open Record Payment modal
      const recordBtn = screen.getByRole('button', { name: /Record Payment/i });
      fireEvent.click(recordBtn);

      expect(screen.getByText('Record Student Payment')).toBeInTheDocument();
    });
  });

  // 3. REFUNDS
  describe('Refunds Page', () => {
    it('renders refund requests and displays approval / rejection buttons', async () => {
      refundsApi.getRefunds.mockResolvedValue({
        items: [
          {
            id: 1,
            refund_id: 'REF-2026-000001',
            student_id: 1,
            student_name: 'Bob Martin',
            student_business_id: 'STU-000003',
            payment_id: 1,
            payment_business_id: 'PAY-2026-000001',
            amount: '15000.00',
            reason: 'Term withdrawal within 100% refund window',
            status: 'REQUESTED',
          },
        ],
        total: 1,
        page: 1,
        pages: 1,
      });

      render(
        <MemoryRouter>
          <Refunds />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Student Refunds & Withdrawals')).toBeInTheDocument();
        expect(screen.getByText('REF-2026-000001')).toBeInTheDocument();
        expect(screen.getByText('Bob Martin')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Approve/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Reject/i })).toBeInTheDocument();
      });
    });
  });

  // 4. LEDGER
  describe('Ledger Page', () => {
    it('renders immutable audit log and allows fetching student statement', async () => {
      ledgerApi.getFinancialEvents.mockResolvedValue({
        items: [
          {
            id: 1,
            event_id: 'EVT-2026-000001',
            event_type: 'INVOICE_GENERATED',
            entity_type: 'Invoice',
            entity_id: '1',
            amount: '75000.00',
            event_timestamp: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        pages: 1,
      });

      render(
        <MemoryRouter>
          <Ledger />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Financial Ledger & Audit Log')).toBeInTheDocument();
        expect(screen.getByText('EVT-2026-000001')).toBeInTheDocument();
        expect(screen.getByText(/DEBIT \(Receivable\)/i)).toBeInTheDocument();
      });

      // Open Statement Modal
      const statementBtn = screen.getByRole('button', { name: /Student Balance Statement/i });
      fireEvent.click(statementBtn);

      expect(screen.getByRole('heading', { name: 'Student Balance Statement' })).toBeInTheDocument();
    });
  });

  // 5. RECONCILIATION
  describe('Reconciliation Page', () => {
    it('renders reconciliation runs and triggers run modal', async () => {
      reconciliationApi.getReconciliationRuns.mockResolvedValue({
        items: [
          {
            id: 1,
            run_id: 'REC-2026-000001',
            run_date: new Date().toISOString(),
            total_invoices: 300,
            matched_count: 295,
            mismatched_count: 5,
            exception_count: 0,
            status: 'COMPLETED',
          },
        ],
        total: 1,
        page: 1,
        pages: 1,
      });

      render(
        <MemoryRouter>
          <Reconciliation />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Financial Reconciliation')).toBeInTheDocument();
        expect(screen.getByText('REC-2026-000001')).toBeInTheDocument();
        expect(screen.getByText('295')).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
      });

      // Open Run Reconciliation modal
      const runBtn = screen.getByRole('button', { name: /Run Reconciliation/i });
      fireEvent.click(runBtn);

      expect(screen.getByText('Execute Reconciliation Run')).toBeInTheDocument();
    });
  });

  // 6. ANOMALIES
  describe('Anomalies Page', () => {
    it('renders anomalies and provides resolution dialog', async () => {
      anomaliesApi.getAnomalies.mockResolvedValue({
        items: [
          {
            id: 1,
            anomaly_id: 'ANM-2026-000001',
            issue_type: 'OVERPAYMENT',
            severity: 'HIGH',
            entity_type: 'Invoice',
            entity_id: '1',
            expected_value: '50000.00',
            actual_value: '60000.00',
            explanation: 'Total payment allocations exceed invoice net amount.',
            resolution_status: 'OPEN',
          },
        ],
        total: 1,
        page: 1,
        pages: 1,
      });

      render(
        <MemoryRouter>
          <Anomalies />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Anomaly Detection & Exceptions')).toBeInTheDocument();
        expect(screen.getByText('ANM-2026-000001')).toBeInTheDocument();
        expect(screen.getByText('OVERPAYMENT')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Resolve/i })).toBeInTheDocument();
      });
    });
  });

  // 7. REPORTS
  describe('Reports Page', () => {
    it('renders real dashboard KPIs and charts container', async () => {
      reportsApi.getDashboardMetrics.mockResolvedValue({
        kpis: {
          total_students: 100,
          active_enrollments: 300,
          total_invoice_value: 20200000.0,
          scholarships_awarded: 0.0,
          payments_collected: 13879350.0,
          outstanding_balance: 1894850.0,
          overdue_invoices: 0,
          late_fees_assessed: 0.0,
          refunds_processed: 16500.0,
          reconciliation_matched: 0,
          reconciliation_mismatched: 0,
          total_anomalies: 5,
          resolved_anomalies: 0,
          unresolved_anomalies: 5,
        },
        charts: {
          invoices_by_status: [{ status: 'PAID', count: 200 }],
          payments_by_status: [{ status: 'COMPLETED', count: 350 }],
          anomalies_by_type: [{ issue_type: 'OVERPAYMENT', count: 2 }],
          outstanding_by_program: [{ program: 'CS-BTECH', outstanding: 207500.0 }],
        },
      });

      render(
        <MemoryRouter>
          <Reports />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Executive Financial Analytics')).toBeInTheDocument();
        expect(screen.getByText('Gross Invoiced')).toBeInTheDocument();
        expect(screen.getByText('Payments Collected')).toBeInTheDocument();
        expect(screen.getByText('Outstanding Balance')).toBeInTheDocument();
        expect(screen.getByText('Outstanding Balance by Academic Program')).toBeInTheDocument();
        expect(screen.getByText('Invoice Portfolio by Status')).toBeInTheDocument();
      });
    });
  });
});
