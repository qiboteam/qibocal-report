import { state, getActiveAuthToken, getServerAuthKey, setServerAuth } from './store.js'
import { getApiUrl, getActiveServerUrl } from './utils/url.js'

/**
 * Dispatches a fetch request against the selected or currently active server,
 * automatically including Authorization headers when a token is present.
 */
export async function apiFetch(path, options = {}, server = state.activeServer) {
  const url = getApiUrl(path, server)
  const headers = new Headers(options.headers || {})
  const token = getActiveAuthToken(server)
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const res = await fetch(url, { ...options, headers })
  if (res.status === 401) noteUnauthorized(server, token)
  return res
}

/**
 * A request was refused for want of a session: forget the token it carried,
 * and — when it concerned the active server — say so and go to the servers
 * page, where one signs in.
 */
function noteUnauthorized(server, token) {
  const serverUrl = getActiveServerUrl(server)
  const sessionIsCurrent = token === getActiveAuthToken(server)
  if (token && sessionIsCurrent) {
    setServerAuth(server, null, null)
  }
  if (sessionIsCurrent && state.auth?.enabled &&
      getServerAuthKey(server) === getServerAuthKey(state.activeServer) &&
      serverUrl === getActiveServerUrl(state.activeServer)) {
    setServerAuth(server, null, null)
    state.auth.errorMessage = 'Authentication required. Please sign in to access this instance.'
    if (typeof window !== 'undefined' && !window.location.hash.startsWith('#/servers') && !window.location.hash.startsWith('#/docs') && !window.location.hash.startsWith('#/invite') && !window.location.hash.startsWith('#/admin')) {
      window.location.hash = '#/servers'
    }
  }
}

/**
 * Which servers answer GraphQL: learnt at the first request, per server.
 * A server from before the endpoint answers the POST with a 404 or a 405,
 * and is asked over REST from then on.
 */
const graphqlSupport = new Map()

function graphqlKey(server) {
  return getActiveServerUrl(server) || 'local'
}

/**
 * Ask several questions in one request, at `/api/graphql`.
 *
 * Answers the `data` of the response; `null` when the server has no such
 * endpoint, which is the caller's cue to ask over REST instead. Errors in
 * the response are thrown, with the first error's code on the exception —
 * `UNAUTHENTICATED` is handled like a 401 before that. The field names are
 * the REST ones, so what comes back is read exactly like a REST response.
 */
export async function apiGraphQL(query, variables = {}, server = state.activeServer, options = {}) {
  const key = graphqlKey(server)
  if (graphqlSupport.get(key) === false) return null
  const token = getActiveAuthToken(server)
  const res = await apiFetch('/api/graphql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, variables }),
    ...options
  }, server)
  if (res.status === 404 || res.status === 405) {
    graphqlSupport.set(key, false)
    return null
  }
  if (!res.ok) throw new Error(`GraphQL request failed (${res.status})`)
  const body = await res.json()
  graphqlSupport.set(key, true)
  if (Array.isArray(body.errors) && body.errors.length) {
    const code = body.errors[0]?.extensions?.code || null
    if (body.errors.some(error => error?.extensions?.code === 'UNAUTHENTICATED')) noteUnauthorized(server, token)
    const failure = new Error(body.errors.map(error => error.message).join('; '))
    failure.code = code
    throw failure
  }
  return body.data
}

/** The fields of a report as the list shows it, for GraphQL selections. */
export const REPORT_FIELDS =
  'id path title date time author platform targets protocols tags labels ' +
  'total_execution_time has_cached_report has_old_platform has_new_platform'

/** The fields of the filter statistics, for GraphQL selections. */
export const STATS_FIELDS =
  'authors tags labels protocols { name count } date_histogram { date count } ' +
  'platforms { name count } author_frequencies { name count } tag_frequencies { name count } total_reports'

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

/** Whether this caller may upload reports to `server`: `{ accepted, auth_enabled }`. */
export async function apiUploadCapability(server) {
  return apiFetch('/api/uploads', { cache: 'no-store' }, server)
}

/** Send a report — the zip of its folder, as a full download gives it — to `server`. */
export async function apiUploadReport(archive, server) {
  return apiFetch('/api/uploads', {
    method: 'POST',
    headers: { 'Content-Type': 'application/zip' },
    body: archive
  }, server)
}

/** Who may upload to the active server, beyond its administrators. Administrators. */
export async function apiGetUploadPolicy(server = state.activeServer) {
  return apiFetch('/api/admin/uploads', { cache: 'no-store' }, server)
}

export async function apiPutUploadPolicy(policy, server = state.activeServer) {
  return apiFetch('/api/admin/uploads', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(policy)
  }, server)
}

/** Gather every report's targets from its protocols, into its meta. Administrators. */
export async function apiInferTargets(server = state.activeServer) {
  return apiFetch('/api/admin/reports/infer-targets', { method: 'POST' }, server)
}

export async function apiGetQibocal(server = state.activeServer) {
  return apiFetch('/api/qibocal', { cache: 'no-store' }, server)
}

export async function apiGetQibocalOptions(server = state.activeServer) {
  return apiFetch('/api/admin/qibocal/options', { cache: 'no-store' }, server)
}

/** The folders under a path on the server, for picking the one Qibocal is installed from. */
export async function apiBrowseServerFolders(path = '', server = state.activeServer) {
  const query = path ? `?path=${encodeURIComponent(path)}` : ''
  return apiFetch(`/api/admin/filesystem${query}`, { cache: 'no-store' }, server)
}

export async function apiInstallQibocal(option, server = state.activeServer) {
  return apiFetch('/api/admin/qibocal/install/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ option })
  }, server)
}

export async function apiStopQibocalInstallation(server = state.activeServer) {
  return apiFetch('/api/admin/qibocal/install/stop', { method: 'POST' }, server)
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

export async function apiGetReportPath(reportId, server = state.activeServer) {
  return apiFetch(`/api/reports/${encodeURIComponent(reportId)}/path`, {
    cache: 'no-store'
  }, server)
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
