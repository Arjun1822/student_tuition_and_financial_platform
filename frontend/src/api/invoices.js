import apiClient from './client';

export const invoicesApi = {
  getInvoices: async (params = {}) => {
    const response = await apiClient.get('/api/v1/invoices/', { params });
    return response.data;
  },

  getInvoice: async (idOrInvoiceId) => {
    const response = await apiClient.get(`/api/v1/invoices/${idOrInvoiceId}`);
    return response.data;
  },

  generateInvoice: async (data) => {
    const response = await apiClient.post('/api/v1/invoices/generate', data);
    return response.data;
  },

  cancelInvoice: async (id, reason) => {
    const response = await apiClient.post(`/api/v1/invoices/${id}/cancel`, { reason });
    return response.data;
  },
};

