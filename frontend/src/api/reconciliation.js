import apiClient from './client';

export const reconciliationApi = {
  triggerReconciliation: async (data = {}) => {
    const response = await apiClient.post('/api/v1/reconciliation/run', data);
    return response.data;
  },

  getReconciliationRuns: async (params = {}) => {
    const response = await apiClient.get('/api/v1/reconciliation/runs', { params });
    return response.data;
  },

  getReconciliationRun: async (id) => {
    const response = await apiClient.get(`/api/v1/reconciliation/runs/${id}`);
    return response.data;
  },

  getReconciliationResults: async (id, params = {}) => {
    const response = await apiClient.get(`/api/v1/reconciliation/runs/${id}/results`, { params });
    return response.data;
  },
};

export default reconciliationApi;
