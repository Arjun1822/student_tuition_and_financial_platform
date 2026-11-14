import apiClient from './client';

export const studentsApi = {
  getStudents: async (params = {}) => {
    const response = await apiClient.get('/api/v1/students/', { params });
    return response.data;
  },

  getStudent: async (idOrSlug) => {
    const response = await apiClient.get(`/api/v1/students/${idOrSlug}`);
    return response.data;
  },

  createStudent: async (data) => {
    const response = await apiClient.post('/api/v1/students/', data);
    return response.data;
  },

  updateStudent: async (idOrSlug, data) => {
    const response = await apiClient.put(`/api/v1/students/${idOrSlug}`, data);
    return response.data;
  },
};

