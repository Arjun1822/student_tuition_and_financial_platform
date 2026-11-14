import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from '../App';

describe('App Root Component', () => {
  it('renders student financial platform branding and redirects unauthenticated user to login', () => {
    render(<App />);
    expect(screen.getByText(/Sign In to StudentFin/i)).toBeInTheDocument();
    expect(screen.getByText(/Student Tuition & Financial Management/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Username/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Password/i)).toBeInTheDocument();
  });
});
