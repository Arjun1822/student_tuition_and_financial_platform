import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from '../App';

describe('App Component', () => {
  it('renders student financial platform branding and milestone status', () => {
    render(<App />);
    expect(screen.getByText(/Student Financial Platform/i)).toBeInTheDocument();
    expect(screen.getByText(/Milestone 1 Verified/i)).toBeInTheDocument();
  });
});
