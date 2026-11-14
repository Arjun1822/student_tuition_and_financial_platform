import apiClient from './client';

export const feeSchedulesApi = {
  getFeeSchedules: async (params = {}) => {
    const response = await apiClient.get('/api/v1/fee-schedules', { params });
    return response.data;
  },

  getFeeSchedule: async (id) => {
    const response = await apiClient.get(`/api/v1/fee-schedules/${id}`);
    return response.data;
  },

  createFeeSchedule: async (data) => {
    const response = await apiClient.post('/api/v1/fee-schedules', data);
    return response.data;
  },

  updateFeeSchedule: async (id, data) => {
    const response = await apiClient.put(`/api/v1/fee-schedules/${id}`, data);
    return response.data;
  },
};

