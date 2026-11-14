import apiClient from './client';

export const scholarshipsApi = {
  getScholarships: async (params = {}) => {
    const response = await apiClient.get('/api/v1/scholarships/', { params });
    return response.data;
  },

  getScholarship: async (idOrSlug) => {
    const response = await apiClient.get(`/api/v1/scholarships/${idOrSlug}`);
    return response.data;
  },

  createScholarship: async (data) => {
    const response = await apiClient.post('/api/v1/scholarships/', data);
    return response.data;
  },

  updateScholarship: async (id, data) => {
    const response = await apiClient.put(`/api/v1/scholarships/${id}`, data);
    return response.data;
  },

  evaluateScholarships: async (data) => {
    const response = await apiClient.post('/api/v1/scholarships/evaluate', data);
    return response.data;
  },

  getEligibilities: async (params = {}) => {
    const response = await apiClient.get('/api/v1/eligibilities/', { params });
    return response.data;
  },

  getEligibility: async (idOrSlug) => {
    const response = await apiClient.get(`/api/v1/eligibilities/${idOrSlug}`);
    return response.data;
  },

  approveEligibility: async (id, data = {}) => {
    const response = await apiClient.post(`/api/v1/eligibilities/${id}/approve`, data);
    return response.data;
  },

  rejectEligibility: async (id, data = {}) => {
    const response = await apiClient.post(`/api/v1/eligibilities/${id}/reject`, data);
    return response.data;
  },
};

export default scholarshipsApi;

