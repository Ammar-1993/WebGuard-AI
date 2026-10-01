/**
 * WebGuard AI — API Client (Axios)
 * ===================================
 * Pre-configured HTTP client for communicating with the Backend API.
 */

import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010';

// ─── Create Axios instance ───
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Interceptor: Auto-attach JWT Token ───
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('webguard_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ─── Interceptor: Handle response errors ───
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired → redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('webguard_token');
        localStorage.removeItem('webguard_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);


// ═══════════════════════════════════════════
//  Auth Functions
// ═══════════════════════════════════════════

export async function register(username, email, password) {
  const response = await api.post('/api/auth/register', { username, email, password });
  const { access_token, user } = response.data;
  localStorage.setItem('webguard_token', access_token);
  localStorage.setItem('webguard_user', JSON.stringify(user));
  return response.data;
}

export async function login(email, password) {
  const response = await api.post('/api/auth/login', { email, password });
  const { access_token, user } = response.data;
  localStorage.setItem('webguard_token', access_token);
  localStorage.setItem('webguard_user', JSON.stringify(user));
  return response.data;
}

export function logout() {
  localStorage.removeItem('webguard_token');
  localStorage.removeItem('webguard_user');
  window.location.href = '/login';
}

export function getCurrentUser() {
  if (typeof window === 'undefined') return null;
  const user = localStorage.getItem('webguard_user');
  return user ? JSON.parse(user) : null;
}

export function isAuthenticated() {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem('webguard_token');
}


// ═══════════════════════════════════════════
//  Scan Functions
// ═══════════════════════════════════════════

export async function startScan(targetUrl) {
  const response = await api.post('/api/scan', { target_url: targetUrl });
  return response.data;
}

export async function getScanStatus(scanId) {
  const response = await api.get(`/api/scan/${scanId}`);
  return response.data;
}


// ═══════════════════════════════════════════
//  Report Functions
// ═══════════════════════════════════════════

export async function getReports() {
  const response = await api.get('/api/reports');
  return response.data;
}

export async function getReportDetail(reportId) {
  const response = await api.get(`/api/reports/${reportId}`);
  return response.data;
}

export async function deleteReport(reportId) {
  await api.delete(`/api/reports/${reportId}`);
}


// ═══════════════════════════════════════════
//  System Health Check
// ═══════════════════════════════════════════

export async function getHealthStatus() {
  const response = await api.get('/health');
  return response.data;
}


// ═══════════════════════════════════════════
//  Error Formatting Helper
// ═══════════════════════════════════════════

/**
 * Safely extracts a clean string error message from any API error,
 * including FastAPI/Pydantic validation errors (array/object formats),
 * ensuring objects are never accidentally passed to React JSX children.
 */
export function extractErrorMessage(err, fallback = 'An unexpected error occurred') {
  if (!err) return fallback;
  if (typeof err === 'string') return err;

  const data = err.response?.data;
  if (data) {
    // 1. Plain string detail
    if (typeof data.detail === 'string') {
      return data.detail;
    }
    // 2. Array of validation error objects (FastAPI / Pydantic v2 format)
    if (Array.isArray(data.detail)) {
      const messages = data.detail.map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          let msg = item.msg || item.message || '';
          if (typeof msg === 'string') {
            msg = msg.replace(/^Value error,\s*/i, '');
          }
          const field = Array.isArray(item.loc) && item.loc.length > 0 ? item.loc[item.loc.length - 1] : null;
          if (field && field !== 'body') {
            const formattedField = field.charAt(0).toUpperCase() + field.slice(1);
            return msg ? `${formattedField}: ${msg}` : formattedField;
          }
          return msg || JSON.stringify(item);
        }
        return String(item);
      }).filter(Boolean);

      if (messages.length > 0) {
        return messages.join(' • ');
      }
    }
    // 3. Single object detail
    if (data.detail && typeof data.detail === 'object') {
      let msg = data.detail.msg || data.detail.message || data.detail.error;
      if (typeof msg === 'string') {
        return msg.replace(/^Value error,\s*/i, '');
      }
      return JSON.stringify(data.detail);
    }
    // 4. Message or Error field at root of response data
    if (typeof data.message === 'string') return data.message;
    if (typeof data.error === 'string') return data.error;
  }

  if (typeof err.message === 'string') {
    return err.message;
  }

  return fallback;
}

export default api;

