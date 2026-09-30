import { state, getActiveAuthToken, getServerAuthKey, setServerAuth } from './store.js'
import { getApiUrl, getActiveServerUrl } from './utils/url.js'

/**
 * Dispatches a fetch request against the selected or currently active server,
 * automatically including Authorization headers when a token is present.
 */
export async function apiFetch(path, options = {}, server = state.activeServer) {
  const url = getApiUrl(path, server)
  const serverUrl = getActiveServerUrl(server)
  const headers = new Headers(options.headers || {})
  const token = getActiveAuthToken(server)
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const res = await fetch(url, { ...options, headers })
  const sessionIsCurrent = token === getActiveAuthToken(server)
  if (res.status === 401 && token && sessionIsCurrent) {
    setServerAuth(server, null, null)
  }
  if (res.status === 401 && sessionIsCurrent && state.auth?.enabled &&
      getServerAuthKey(server) === getServerAuthKey(state.activeServer) &&
      serverUrl === getActiveServerUrl(state.activeServer)) {
    setServerAuth(server, null, null)
    state.auth.errorMessage = 'Authentication required. Please sign in to access this instance.'
    if (typeof window !== 'undefined' && !window.location.hash.startsWith('#/servers') && !window.location.hash.startsWith('#/docs') && !window.location.hash.startsWith('#/invite') && !window.location.hash.startsWith('#/admin')) {
      window.location.hash = '#/servers'
    }
  }
  return res
}

/**
 * Authentication & Role Management endpoints.
 */
export async function apiGetAuthStatus(server = state.activeServer) {
  const base = getActiveServerUrl(server)
  const url = base ? `${base}/api/auth/status` : '/api/auth/status'
  return fetch(url, { cache: 'no-store' })
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

export async function apiGetPasswordReset(token, server = state.activeServer) {
  const base = getActiveServerUrl(server)
  const url = base ? `${base}/api/auth/password-reset/${encodeURIComponent(token)}` : `/api/auth/password-reset/${encodeURIComponent(token)}`
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

export async function apiGetQibocal(server = state.activeServer) {
  return apiFetch('/api/qibocal', { cache: 'no-store' }, server)
}

export async function apiGetQibocalOptions(server = state.activeServer) {
  return apiFetch('/api/admin/qibocal/options', { cache: 'no-store' }, server)
}

export async function apiInstallQibocal(option, server = state.activeServer) {
  return apiFetch('/api/admin/qibocal/install/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ option })
  }, server)
}

export async function apiGetServerLogs(after, server = state.activeServer, signal) {
  return apiFetch(`/api/admin/logs?after=${encodeURIComponent(after)}`, {
    cache: 'no-store',
    signal
  }, server)
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
