import apiClient from './client';

export const ledgerApi = {
  getFinancialEvents: async (params = {}) => {
    const response = await apiClient.get('/api/v1/ledger/events', { params });
    return response.data;
  },

  getStudentStatement: async (studentId) => {
    const response = await apiClient.get(`/api/v1/ledger/students/${studentId}/statement`);
    return response.data;
  },

  assessLateFee: async (invoiceId, data = {}) => {
    const response = await apiClient.post(`/api/v1/ledger/invoices/${invoiceId}/late-fee`, data);
    return response.data;
  },
};

export default ledgerApi;
