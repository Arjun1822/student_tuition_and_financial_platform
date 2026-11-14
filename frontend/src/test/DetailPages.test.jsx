import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ProgramDetails from '../pages/ProgramDetails';
import EnrollmentDetails from '../pages/EnrollmentDetails';
import InvoiceDetails from '../pages/InvoiceDetails';
import { programsApi } from '../api/programs';
import { feeSchedulesApi } from '../api/feeSchedules';
import { enrollmentsApi } from '../api/enrollments';
import { invoicesApi } from '../api/invoices';

// Mock API modules
vi.mock('../api/programs');
vi.mock('../api/feeSchedules');
vi.mock('../api/enrollments');
vi.mock('../api/invoices');

describe('Frontend Detail Pages & Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('ProgramDetails Component', () => {
    it('renders loading state initially, then displays program details and fee schedules', async () => {
      const mockProgram = {
        id: 1,
        program_id: 'PRG-000001',
        name: 'Computer Science and Engineering',
        code: 'PRG-000001',
        department: 'Computer Science',
        degree_level: 'BACHELOR',
        duration_years: 4,
        total_credits: 120,
        status: 'ACTIVE',
        description: 'Comprehensive software engineering and computing curriculum.',
      };

      const mockFeeSchedules = {
        items: [
          {
            id: 1,
            fee_schedule_id: 'FEE-000001',
            program_id: 1,
            term_id: 1,
            tuition_fee: '50000.00',
            total_fee: '60000.00',
            is_active: true,
            term: { name: 'Fall 2026' },
          },
        ],
      };

      programsApi.getProgram.mockResolvedValue(mockProgram);
      feeSchedulesApi.getFeeSchedules.mockResolvedValue(mockFeeSchedules);

      render(
        <MemoryRouter
          initialEntries={['/programs/1']}
          future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
        >
          <Routes>
            <Route path="/programs/:id" element={<ProgramDetails />} />
          </Routes>
        </MemoryRouter>
      );

      // Loading state
      expect(screen.getByText(/Loading program details/i)).toBeInTheDocument();

      // Resolved data
      await waitFor(() => {
        expect(screen.getByText('Computer Science and Engineering')).toBeInTheDocument();
      });

      expect(screen.getByText('Computer Science')).toBeInTheDocument();
      expect(screen.getByText('BACHELOR')).toBeInTheDocument();
      expect(screen.getByText('FEE-000001')).toBeInTheDocument();
      expect(screen.getByText('INR 60,000')).toBeInTheDocument();
    });

    it('renders error state when program fetch fails', async () => {
      programsApi.getProgram.mockRejectedValue({
        response: { data: { detail: 'Program not found' } },
      });

      render(
        <MemoryRouter
          initialEntries={['/programs/999']}
          future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
        >
          <Routes>
            <Route path="/programs/:id" element={<ProgramDetails />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Program not found')).toBeInTheDocument();
      });
      expect(screen.getByText(/Back to Programs/i)).toBeInTheDocument();
    });
  });

  describe('EnrollmentDetails Component', () => {
    it('renders student, program, term details and associated invoices', async () => {
      const mockEnrollment = {
        id: 1,
        enrollment_id: 'ENR-000001',
        student_id: 1,
        program_id: 1,
        term_id: 1,
        status: 'ACTIVE',
        enrollment_date: '2026-08-01',
        student: {
          id: 1,
          student_id: 'STU-000001',
          first_name: 'Aarav',
          last_name: 'Sharma',
          email: 'aarav.sharma@test.edu',
        },
        program: {
          id: 1,
          name: 'Computer Science and Engineering',
          code: 'PRG-000001',
          department: 'Computer Science',
        },
        term: {
          id: 1,
          term_id: 'TERM-2026-FALL',
          name: 'Fall 2026',
          year: 2026,
          semester: 'FALL',
        },
      };

      const mockInvoices = {
        items: [
          {
            id: 1,
            invoice_id: 'INV-STU-000001-2026-000001',
            billing_cycle: '2026-FALL',
            gross_amount: '60000.00',
            scholarship_discount: '30000.00',
            net_amount: '30000.00',
            amount_paid: '10000.00',
            outstanding_balance: '20000.00',
            status: 'PARTIALLY_PAID',
          },
        ],
      };

      enrollmentsApi.getEnrollment.mockResolvedValue(mockEnrollment);
      invoicesApi.getInvoices.mockResolvedValue(mockInvoices);

      render(
        <MemoryRouter
          initialEntries={['/enrollments/1']}
          future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
        >
          <Routes>
            <Route path="/enrollments/:id" element={<EnrollmentDetails />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('ENR-000001')).toBeInTheDocument();
      });

      expect(screen.getByText('Aarav Sharma')).toBeInTheDocument();
      expect(screen.getByText('Computer Science and Engineering')).toBeInTheDocument();
      expect(screen.getByText('Fall 2026')).toBeInTheDocument();
      expect(screen.getByText('INV-STU-000001-2026-000001')).toBeInTheDocument();
      expect(screen.getByText('Generate Invoice')).toBeInTheDocument();
    });
  });

  describe('InvoiceDetails Component', () => {
    it('renders financial summary metrics and line items breakdown', async () => {
      const mockInvoice = {
        id: 1,
        invoice_id: 'INV-STU-000001-2026-000001',
        billing_cycle: '2026-FALL',
        invoice_date: '2026-08-01',
        due_date: '2026-08-31',
        gross_amount: '60000.00',
        scholarship_discount: '30000.00',
        net_amount: '30000.00',
        amount_paid: '10000.00',
        outstanding_balance: '20000.00',
        status: 'PARTIALLY_PAID',
        notes: 'Fall semester regular billing',
        student: {
          id: 1,
          student_id: 'STU-000001',
          first_name: 'Aarav',
          last_name: 'Sharma',
        },
        term: {
          name: 'Fall 2026',
        },
        lines: [
          {
            id: 1,
            invoice_line_id: 'INVL-000001',
            fee_type: 'TUITION',
            description: 'Tuition Fee - Computer Science',
            amount: '50000.00',
            allocated_amount: '10000.00',
            remaining_amount: '40000.00',
          },
          {
            id: 2,
            invoice_line_id: 'INVL-000002',
            fee_type: 'LABORATORY',
            description: 'Laboratory Fee - Computer Science',
            amount: '10000.00',
            allocated_amount: '0.00',
            remaining_amount: '10000.00',
          },
        ],
      };

      invoicesApi.getInvoice.mockResolvedValue(mockInvoice);

      render(
        <MemoryRouter
          initialEntries={['/invoices/1']}
          future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
        >
          <Routes>
            <Route path="/invoices/:id" element={<InvoiceDetails />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('INV-STU-000001-2026-000001')).toBeInTheDocument();
      });

      expect(screen.getByText('Aarav Sharma')).toBeInTheDocument();
      expect(screen.getByText('INR 60,000')).toBeInTheDocument();
      expect(screen.getByText('-INR 30,000')).toBeInTheDocument();
      expect(screen.getByText('INR 30,000')).toBeInTheDocument();
      expect(screen.getByText('INR 20,000')).toBeInTheDocument();
      expect(screen.getByText('INVL-000001')).toBeInTheDocument();
      expect(screen.getByText('Tuition Fee - Computer Science')).toBeInTheDocument();
      expect(screen.getByText('Cancel Invoice')).toBeInTheDocument();
    });
  });
});
