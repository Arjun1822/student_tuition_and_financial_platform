import apiClient from './client';

export const programsApi = {
  getPrograms: async (params = {}) => {
    const response = await apiClient.get('/api/v1/programs/', { params });
    return response.data;
  },

  getProgram: async (idOrCode) => {
    const response = await apiClient.get(`/api/v1/programs/${idOrCode}`);
    return response.data;
  },

  createProgram: async (data) => {
    const response = await apiClient.post('/api/v1/programs/', data);
    return response.data;
  },

  updateProgram: async (idOrCode, data) => {
    const response = await apiClient.put(`/api/v1/programs/${idOrCode}`, data);
    return response.data;
  },
};

