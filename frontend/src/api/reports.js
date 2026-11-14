import apiClient from './client';

export const reportsApi = {
  getDashboardMetrics: async () => {
    const response = await apiClient.get('/api/v1/reports/dashboard');
    return response.data;
  },
};

export default reportsApi;
