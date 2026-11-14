import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Interceptor to inject JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor to handle authentication errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response ? error.response.status : null;
    const isLoginEndpoint = error.config?.url?.includes('/api/v1/auth/login');

    // 401 Unauthorized triggers reauthentication only for protected endpoints when the token is genuinely invalid or expired.
    // Login requests returning 401 should display invalid credentials in the form rather than redirecting.
    if (status === 401 && !isLoginEndpoint) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    // 403 Forbidden indicates an authorization/permission refusal: preserve the session and let the UI display the error message.
    return Promise.reject(error);
  }
);

export default apiClient;

