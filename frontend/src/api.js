import { state } from './store.js'
import { getApiUrl } from './utils/url.js'

/**
 * Dispatches a fetch request against the currently active server's base URL.
 */
export async function apiFetch(path, options = {}) {
  const url = getApiUrl(path, state.activeServer)
  return fetch(url, options)
}

/**
 * Server management API endpoints.
 */
export async function apiGetServers() {
  return fetch('/api/servers')
}

export async function apiCreateServer(payload) {
  return fetch('/api/servers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function apiUpdateServer(id, payload) {
  return fetch(`/api/servers/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function apiDeleteServer(id) {
  return fetch(`/api/servers/${id}`, { method: 'DELETE' })
}

export async function apiPersistServers() {
  return fetch('/api/servers/save', { method: 'POST' })
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
