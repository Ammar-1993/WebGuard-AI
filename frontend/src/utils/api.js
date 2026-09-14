/**
 * WebGuard AI — API Client (Axios)
 * ===================================
 * عميل HTTP مُهيّأ مسبقاً للتواصل مع الخادم المركزي (Backend API).
 */

import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010';

// ─── إنشاء عميل Axios ───
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Interceptor: إضافة JWT Token تلقائياً ───
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('webguard_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ─── Interceptor: معالجة أخطاء الاستجابة ───
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // إذا انتهت صلاحية الـ Token → إعادة توجيه لتسجيل الدخول
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
//  دوال المصادقة (Auth)
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
//  دوال الفحص الأمني (Scan)
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
//  دوال التقارير (Reports)
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
//  فحص صحة النظام
// ═══════════════════════════════════════════

export async function getHealthStatus() {
  const response = await api.get('/health');
  return response.data;
}

export default api;
