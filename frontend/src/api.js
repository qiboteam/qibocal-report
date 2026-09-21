import { state, getActiveAuthToken } from './store.js'
import { getApiUrl, getActiveServerUrl } from './utils/url.js'

/**
 * Dispatches a fetch request against the currently active server's base URL,
 * automatically including Authorization headers when a token is present.
 */
export async function apiFetch(path, options = {}) {
  const url = getApiUrl(path, state.activeServer)
  const headers = new Headers(options.headers || {})
  const token = getActiveAuthToken(state.activeServer)
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const res = await fetch(url, { ...options, headers })
  if (res.status === 401 && state.auth?.enabled) {
    state.auth.token = null
    state.auth.user = null
    state.auth.errorMessage = 'Authentication required. Please sign in to access this instance.'
    if (typeof window !== 'undefined' && !window.location.hash.startsWith('#/servers') && !window.location.hash.startsWith('#/docs') && !window.location.hash.startsWith('#/invite')) {
      window.location.hash = '#/servers'
    }
  }
  return res
}

/**
 * Server management API endpoints.
 */
export async function apiGetServers() {
  return fetch('/api/servers')
}

export async function apiCreateServer(payload) {
  return apiFetch('/api/servers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function apiUpdateServer(id, payload) {
  return apiFetch(`/api/servers/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function apiDeleteServer(id) {
  return apiFetch(`/api/servers/${id}`, { method: 'DELETE' })
}

export async function apiPersistServers() {
  return apiFetch('/api/servers/save', { method: 'POST' })
}

/**
 * Authentication & Role Management endpoints.
 */
export async function apiGetAuthStatus(server = state.activeServer) {
  const base = getActiveServerUrl(server)
  const url = base ? `${base}/api/auth/status` : '/api/auth/status'
  return fetch(url)
}

export async function apiLogin(username, password, server = state.activeServer) {
  const base = getActiveServerUrl(server)
  const url = base ? `${base}/api/auth/login` : '/api/auth/login'
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
}

export async function apiGetMe(token, server = state.activeServer) {
  const base = getActiveServerUrl(server)
  const url = base ? `${base}/api/auth/me` : '/api/auth/me'
  return fetch(url, {
    headers: { Authorization: `Bearer ${token}` }
  })
}

export async function apiGetInvite(token, server = state.activeServer) {
  const base = getActiveServerUrl(server)
  const url = base ? `${base}/api/auth/invite/${encodeURIComponent(token)}` : `/api/auth/invite/${encodeURIComponent(token)}`
  return fetch(url)
}

export async function apiRegister(inviteToken, username, password, server = state.activeServer) {
  const base = getActiveServerUrl(server)
  const url = base ? `${base}/api/auth/register` : '/api/auth/register'
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      invite_token: inviteToken,
      username,
      password
    })
  })
}

/**
 * Admin Role & Invites API endpoints.
 */
export async function apiGetAdminUsers() {
  return apiFetch('/api/admin/users')
}

export async function apiUpdateUserRole(userId, role) {
  return apiFetch(`/api/admin/users/${encodeURIComponent(userId)}/role`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role })
  })
}

export async function apiDeleteUser(userId) {
  return apiFetch(`/api/admin/users/${encodeURIComponent(userId)}`, {
    method: 'DELETE'
  })
}

export async function apiGetAdminInvites() {
  return apiFetch('/api/admin/invites')
}

export async function apiCreateInvite(payload) {
  return apiFetch('/api/admin/invites', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function apiDeleteInvite(token) {
  return apiFetch(`/api/admin/invites/${encodeURIComponent(token)}`, {
    method: 'DELETE'
  })
}

export async function apiGetAdminPasswordResets() {
  return apiFetch('/api/admin/password-resets')
}

export async function apiCreatePasswordReset(userId) {
  return apiFetch('/api/admin/password-resets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId })
  })
}

export async function apiDeletePasswordReset(token) {
  return apiFetch(`/api/admin/password-resets/${encodeURIComponent(token)}`, {
    method: 'DELETE'
  })
}

export async function apiGetAdminConfig() {
  return apiFetch('/api/admin/config')
}

/**
 * Report queries and actions API endpoints.
 */
export async function apiGetReportStats() {
  return apiFetch('/api/reports/stats')
}

export async function apiGetReports(searchParams) {
  const queryStr = searchParams ? `?${searchParams.toString()}` : ''
  return apiFetch(`/api/reports${queryStr}`)
}

export async function apiGetReport(reportId) {
  const encodedId = encodeURIComponent(reportId)
  return apiFetch(`/api/reports/${encodedId}`)
}

export async function apiGetReportProtocols(reportId) {
  const encodedId = encodeURIComponent(reportId)
  return apiFetch(`/api/reports/${encodedId}/protocols`)
}

export async function apiRegenerateReport(reportId) {
  const encodedId = encodeURIComponent(reportId)
  return apiFetch(`/api/reports/${encodedId}/regenerate`, { method: 'POST' })
}

export async function apiUpdateReportAuthor(reportId, author) {
  const encodedId = encodeURIComponent(reportId)
  return apiFetch(`/api/reports/${encodedId}/author`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ author })
  })
}

export async function apiDeleteReportTag(reportId, tag) {
  const encodedId = encodeURIComponent(reportId)
  const encodedTag = encodeURIComponent(tag)
  return apiFetch(`/api/reports/${encodedId}/label/${encodedTag}`, {
    method: 'DELETE'
  })
}

export async function apiBulkAction(payload) {
  return apiFetch('/api/reports/bulk-action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

