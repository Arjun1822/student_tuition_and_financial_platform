import apiClient from './client';

export const paymentsApi = {
  getPayments: async (params = {}) => {
    const response = await apiClient.get('/api/v1/payments', { params });
    return response.data;
  },

  getPayment: async (idOrSlug) => {
    const response = await apiClient.get(`/api/v1/payments/${idOrSlug}`);
    return response.data;
  },

  recordPayment: async (data) => {
    const response = await apiClient.post('/api/v1/payments', data);
    return response.data;
  },

  allocatePayment: async (id, data) => {
    const response = await apiClient.post(`/api/v1/payments/${id}/allocate`, data);
    return response.data;
  },

  reversePayment: async (id, data) => {
    const response = await apiClient.post(`/api/v1/payments/${id}/reverse`, data);
    return response.data;
  },

  getPaymentAllocations: async (params = {}) => {
    const response = await apiClient.get('/api/v1/payment-allocations', { params });
    return response.data;
  },
};

export default paymentsApi;

