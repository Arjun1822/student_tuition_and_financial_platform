import apiClient from './client';

export const refundsApi = {
  getRefunds: async (params = {}) => {
    const response = await apiClient.get('/api/v1/refunds/', { params });
    return response.data;
  },

  getRefund: async (idOrSlug) => {
    const response = await apiClient.get(`/api/v1/refunds/${idOrSlug}`);
    return response.data;
  },

  requestRefund: async (data) => {
    const response = await apiClient.post('/api/v1/refunds/', data);
    return response.data;
  },

  approveRefund: async (id, data = {}) => {
    const response = await apiClient.post(`/api/v1/refunds/${id}/approve`, data);
    return response.data;
  },

  processRefund: async (id) => {
    const response = await apiClient.post(`/api/v1/refunds/${id}/process`);
    return response.data;
  },

  rejectRefund: async (id, data = {}) => {
    const response = await apiClient.post(`/api/v1/refunds/${id}/reject`, data);
    return response.data;
  },
};

export default refundsApi;
