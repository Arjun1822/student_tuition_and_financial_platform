import apiClient from './client';

export const enrollmentsApi = {
  getEnrollments: async (params = {}) => {
    const response = await apiClient.get('/api/v1/enrollments/', { params });
    return response.data;
  },

  getEnrollment: async (idOrSlug) => {
    const response = await apiClient.get(`/api/v1/enrollments/${idOrSlug}`);
    return response.data;
  },

  createEnrollment: async (data) => {
    const response = await apiClient.post('/api/v1/enrollments/', data);
    return response.data;
  },

  cancelEnrollment: async (id, reason) => {
    const response = await apiClient.post(`/api/v1/enrollments/${id}/cancel`, { reason });
    return response.data;
  },

  withdrawEnrollment: async (id, reason) => {
    const response = await apiClient.post(`/api/v1/enrollments/${id}/withdraw`, { reason });
    return response.data;
  },
};

