import apiClient from './client';

export const anomaliesApi = {
  getAnomalies: async (params = {}) => {
    const response = await apiClient.get('/api/v1/anomalies', { params });
    return response.data;
  },

  getAnomaly: async (idOrSlug) => {
    const response = await apiClient.get(`/api/v1/anomalies/${idOrSlug}`);
    return response.data;
  },

  triggerAnomalyScan: async () => {
    const response = await apiClient.post('/api/v1/anomalies/scan');
    return response.data;
  },

  resolveAnomaly: async (id, data) => {
    const response = await apiClient.post(`/api/v1/anomalies/${id}/resolve`, data);
    return response.data;
  },
};

export default anomaliesApi;

