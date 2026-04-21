/**
 * API Client — Wrapper fetch con JWT auto-refresh.
 *
 * Gestiona automáticamente:
 * - Inyección del header Authorization con el access token
 * - Refresh automático del token cuando expira (401)
 * - Reintentos tras refresh exitoso
 * - Logout automático si el refresh falla
 */

const API_BASE = 'http://localhost:8000';

// ─── Token helpers ───────────────────────────────────

export function getTokens() {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  };
}

export function setTokens(access, refresh) {
  localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_info');
}

// ─── Core fetch ──────────────────────────────────────

async function refreshAccessToken() {
  const { refresh } = getTokens();
  if (!refresh) return null;

  const res = await fetch(`${API_BASE}/api/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) {
    clearTokens();
    return null;
  }

  const data = await res.json();
  setTokens(data.access, data.refresh || refresh);
  return data.access;
}

async function apiFetch(endpoint, options = {}, _retry = false) {
  const { access } = getTokens();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (access) {
    headers['Authorization'] = `Bearer ${access}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  // Auto-refresh en 401 (solo un reintento)
  if (res.status === 401 && !_retry) {
    const newAccess = await refreshAccessToken();
    if (newAccess) {
      return apiFetch(endpoint, options, true);
    }
    // Refresh falló → forzar logout
    clearTokens();
    window.dispatchEvent(new Event('auth:logout'));
    throw new Error('Sesión expirada. Por favor inicie sesión nuevamente.');
  }

  return res;
}

// ─── Public API ──────────────────────────────────────

export async function api(endpoint, options = {}) {
  const res = await apiFetch(endpoint, options);

  if (res.status === 204) return null;

  const data = await res.json();

  if (!res.ok) {
    const error = new Error('Error de API');
    error.status = res.status;
    error.data = data;
    throw error;
  }

  return data;
}

export const apiGet = (endpoint) => api(endpoint);

export const apiPost = (endpoint, body) =>
  api(endpoint, { method: 'POST', body: JSON.stringify(body) });

export const apiPut = (endpoint, body) =>
  api(endpoint, { method: 'PUT', body: JSON.stringify(body) });

export const apiPatch = (endpoint, body) =>
  api(endpoint, { method: 'PATCH', body: JSON.stringify(body) });

export const apiDelete = (endpoint) =>
  api(endpoint, { method: 'DELETE' });

// ─── Auth endpoints ──────────────────────────────────

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/api/auth/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  const data = await res.json();
  if (!res.ok) {
    const error = new Error('Credenciales inválidas');
    error.data = data;
    throw error;
  }

  setTokens(data.access, data.refresh);
  return data;
}

export async function registro(formData) {
  const res = await fetch(`${API_BASE}/api/auth/registro/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData),
  });

  const data = await res.json();
  if (!res.ok) {
    const error = new Error('Error en el registro');
    error.data = data;
    throw error;
  }

  return data;
}
