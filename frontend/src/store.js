import { reactive, computed, watch } from 'vue'
import { CLIENT_LAYOUT_KEYS, parseClientServer, parseClientState } from './utils/clientState.js'
import {
  normalizeUrl as utilsNormalizeUrl,
  getActiveServerUrl as utilsGetActiveServerUrl,
  getApiUrl as utilsGetApiUrl,
  getActiveWsUrl as utilsGetActiveWsUrl
} from './utils/url.js'

// --- Initial Local Storage State ---
let initialHistory = []
try {
  const savedHistory = localStorage.getItem('qibocal_report_history')
  if (savedHistory) {
    const parsed = JSON.parse(savedHistory)
    if (Array.isArray(parsed)) {
      initialHistory = parsed
    }
  }
} catch (e) {
  console.warn('Failed to parse saved history from localStorage', e)
}

// --- Storage Keys ---
const SEARCH_STATE_STORAGE_KEY = 'qibocal_report_search_state'
const SERVERS_STORAGE_KEY = 'qibocal_report_servers'

function loadStoredServers() {
  try {
    const raw = localStorage.getItem(SERVERS_STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) {
        return parsed
      }
    }
  } catch (e) {
    console.error('Failed to parse saved servers from localStorage', e)
  }
  return []
}

function loadSidebarPreference() {
  try {
    return localStorage.getItem('qibocal_report_sidebar_collapsed') === 'true'
  } catch (error) {
    console.warn('Failed to load sidebar preference', error)
    return false
  }
}

// --- Search State Persistence (Session Storage) ---
function loadSavedSearchState() {
  try {
    const raw = sessionStorage.getItem(SEARCH_STATE_STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      return {
        serverId: parsed.serverId || null,
        filters: {
          q: parsed.filters?.q || '',
          author: parsed.filters?.author || '',
          platform: parsed.filters?.platform || '',
          folder: parsed.filters?.folder || '',
          date: parsed.filters?.date || '',
          startDate: parsed.filters?.startDate || parsed.filters?.date || '',
          endDate: parsed.filters?.endDate || parsed.filters?.date || '',
          protocols: Array.isArray(parsed.filters?.protocols) ? parsed.filters.protocols : [],
          labels: Array.isArray(parsed.filters?.labels) ? parsed.filters.labels : [],
          qubits: Array.isArray(parsed.filters?.qubits) ? parsed.filters.qubits : [],
          sort_by: parsed.filters?.sort_by || 'date_desc'
        },
        currentPage: typeof parsed.currentPage === 'number' ? parsed.currentPage : 1,
        pageSize: typeof parsed.pageSize === 'number' ? parsed.pageSize : 10
      }
    }
  } catch (e) {
    console.warn('Failed to load search state from sessionStorage', e)
  }
  return {
    serverId: null,
    filters: {
      q: '',
      author: '',
      platform: '',
      folder: '',
      date: '',
      startDate: '',
      endDate: '',
      protocols: [],
      labels: [],
      qubits: [],
      sort_by: 'date_desc'
    },
    currentPage: 1,
    pageSize: 10
  }
}

/**
 * Global reactive application store.
 */
export const state = reactive({
  servers: loadStoredServers(),
  activeServer: null,
  history: initialHistory,
  currentReportId: null,
  currentReportData: null,
  sidebarCollapsed: loadSidebarPreference(),
  loading: false,
  error: null,
  serverDataVersion: 0,
  pendingFilter: null,
  searchState: loadSavedSearchState(),
  auth: {
    enabled: false,
    checked: false,
    token: null,
    user: null,
    showLoginModal: false,
    showRegisterModal: false,
    registerData: null,
    errorMessage: ''
  }
})

watch(() => state.sidebarCollapsed, value => {
  try {
    localStorage.setItem('qibocal_report_sidebar_collapsed', String(value))
  } catch (error) {
    console.warn('Failed to save sidebar preference', error)
  }
})

// Restore active server from localStorage
if (state.servers.length > 0) {
  const savedActiveId = localStorage.getItem('qibocal_active_server_id')
  if (savedActiveId) {
    const found = state.servers.find(s => s.id === savedActiveId)
    if (found) {
      state.activeServer = found
    } else if (state.servers.length > 0) {
      state.activeServer = state.servers[0]
    }
  } else if (state.servers.length > 0) {
    state.activeServer = state.servers[0]
  }
}

// --- Auth Storage & Helpers ---
const AUTH_STORAGE_KEY = 'qibocal_report_auth'

function loadStoredAuth() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (typeof parsed === 'object' && parsed !== null) return parsed
    }
  } catch (e) {
    console.warn('Failed to parse auth from localStorage', e)
  }
  return {}
}

function saveStoredAuth(authMap) {
  try {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authMap))
  } catch (e) {
    console.warn('Failed to save auth to localStorage', e)
  }
}

const serverAuth = reactive(loadStoredAuth())
let authCheckVersion = 0
let clientStateVersion = 0
let pendingAuthCheck = null

export function getServerAuthKey(server = state.activeServer) {
  if (!server) return 'local'
  if (server.id) return server.id
  return normalizeUrl(server.url) || 'local'
}

export function getActiveAuthToken(server = state.activeServer) {
  const key = getServerAuthKey(server)
  return serverAuth[key]?.token || null
}

export function getActiveUser(server = state.activeServer) {
  const key = getServerAuthKey(server)
  return serverAuth[key]?.user || null
}

export function getAuthHeader(server = state.activeServer) {
  const token = getActiveAuthToken(server)
  if (token) {
    return { Authorization: `Bearer ${token}` }
  }
  return {}
}

export function setServerAuth(server, token, user) {
  const key = getServerAuthKey(server)
  if (token && user) {
    serverAuth[key] = { token, user }
  } else {
    delete serverAuth[key]
  }
  saveStoredAuth(serverAuth)

  if (key === getServerAuthKey(state.activeServer)) {
    state.auth.token = token
    state.auth.user = user
  }
}

// --- Role Computed Getters ---
export const isViewer = computed(() => {
  return Boolean(state.auth?.enabled && state.auth?.user?.role === 'viewer')
})

export const canEdit = computed(() => {
  if (!state.auth?.enabled) return true
  const role = state.auth?.user?.role
  return role === 'editor' || role === 'admin'
})

export const isAdmin = computed(() => {
  if (!state.auth?.enabled) return true
  return state.auth?.user?.role === 'admin'
})

export const isAuthenticated = computed(() => {
  if (!state.auth?.enabled) return true
  return Boolean(state.auth?.token && state.auth?.user)
})

export const canAccessDashboard = computed(() => {
  if (!state.activeServer || state.servers.length === 0) return false
  if (!state.servers.some(s => s.id === state.activeServer?.id)) return false
  if (state.auth?.enabled && (!state.auth?.token || !state.auth?.user)) return false
  return true
})

export function checkActiveServerAuth(targetServer = state.activeServer) {
  if (!targetServer) return Promise.resolve(false)
  const key = getServerAuthKey(targetServer)
  if (pendingAuthCheck?.key === key && pendingAuthCheck.version === authCheckVersion) {
    return pendingAuthCheck.promise
  }
  const version = ++authCheckVersion
  const promise = verifyServerAuth(targetServer, version)
  pendingAuthCheck = { key, version, promise }
  promise.finally(() => {
    if (pendingAuthCheck?.promise === promise) pendingAuthCheck = null
  })
  return promise
}

async function verifyServerAuth(targetServer, version) {
  const isCurrent = () => version === authCheckVersion &&
    getServerAuthKey(targetServer) === getServerAuthKey(state.activeServer)
  const serverUrl = getActiveServerUrl(targetServer)
  const statusUrl = serverUrl ? `${serverUrl}/api/auth/status` : '/api/auth/status'

  try {
    const res = await fetch(statusUrl, { signal: AbortSignal.timeout(4000), cache: 'no-store' })
    if (!res.ok) throw new Error(`Authentication status request failed (${res.status})`)
    const data = await res.json()
    let token = null
    let user = null
    if (data.auth_enabled) {
      token = getActiveAuthToken(targetServer)
      if (token) {
        const meUrl = serverUrl ? `${serverUrl}/api/auth/me` : '/api/auth/me'
        const meRes = await fetch(meUrl, {
          headers: { Authorization: `Bearer ${token}` },
          signal: AbortSignal.timeout(4000),
          cache: 'no-store'
        })
        if (meRes.ok) {
          user = await meRes.json()
        } else if (meRes.status === 401) {
          token = null
        } else {
          throw new Error(`Session validation failed (${meRes.status})`)
        }
      }
    }
    if (!isCurrent()) return false
    setServerAuth(targetServer, token, user)
    state.auth.enabled = Boolean(data.auth_enabled)
    state.auth.checked = true
    state.auth.user = data.auth_enabled ? user : { id: 'admin', username: 'local-admin', role: 'admin' }
    state.auth.errorMessage = ''
    return true
  } catch (e) {
    if (!isCurrent()) return false
    console.warn('Failed to check auth status for server', e)
    state.auth.enabled = true
    state.auth.checked = false
    state.auth.token = null
    state.auth.user = null
    state.auth.errorMessage = `Cannot verify authentication for "${targetServer.name}": ${e.message}`
    return false
  }
}

export async function loginActiveServer(username, password) {
  const version = clientStateVersion
  const server = state.activeServer
  const serverUrl = getActiveServerUrl(server)
  const loginUrl = serverUrl ? `${serverUrl}/api/auth/login` : '/api/auth/login'

  const res = await fetch(loginUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Login failed')
  }

  const data = await res.json()
  if (version !== clientStateVersion) throw new Error('Client state changed. Please sign in again.')
  if (getServerAuthKey(server) === getServerAuthKey(state.activeServer)) authCheckVersion++
  setServerAuth(server, data.access_token, data.user)
  state.auth.errorMessage = ''
  notifyServerDataChanged()
  return data
}

export function logoutActiveServer(server = state.activeServer) {
  if (getServerAuthKey(server) === getServerAuthKey(state.activeServer)) {
    authCheckVersion++
    state.auth.showLoginModal = false
    state.auth.errorMessage = ''
  }
  setServerAuth(server, null, null)
  notifyServerDataChanged()
}

export async function registerWithInvite(inviteToken, username, password, targetServer = state.activeServer) {
  const version = clientStateVersion
  const serverUrl = getActiveServerUrl(targetServer)
  const regUrl = serverUrl ? `${serverUrl}/api/auth/register` : '/api/auth/register'

  const res = await fetch(regUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      invite_token: inviteToken,
      username,
      password
    })
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Registration failed')
  }

  const data = await res.json()
  if (version !== clientStateVersion) throw new Error('Client state changed. Please sign in again.')
  if (getServerAuthKey(targetServer) === getServerAuthKey(state.activeServer)) authCheckVersion++
  setServerAuth(targetServer, data.access_token, data.user)
  notifyServerDataChanged()
  return data
}

export function persistSearchState() {
  try {
    const currentServerId = state.activeServer?.id || state.activeServer?.url || 'local'
    state.searchState.serverId = currentServerId
    sessionStorage.setItem(SEARCH_STATE_STORAGE_KEY, JSON.stringify(state.searchState))
  } catch (e) {
    console.warn('Failed to save search state to sessionStorage', e)
  }
}

export function resetSearchState() {
  state.searchState.filters.q = ''
  state.searchState.filters.author = ''
  state.searchState.filters.platform = ''
  state.searchState.filters.folder = ''
  state.searchState.filters.date = ''
  state.searchState.filters.startDate = ''
  state.searchState.filters.endDate = ''
  state.searchState.filters.protocols = []
  state.searchState.filters.labels = []
  state.searchState.filters.qubits = []
  state.searchState.filters.sort_by = 'date_desc'
  state.searchState.currentPage = 1
  persistSearchState()
}

export function hasActiveSearchFilters(filters = state.searchState?.filters) {
  if (!filters) return false
  return Boolean(
    (filters.q && filters.q.trim()) ||
    filters.author ||
    filters.platform ||
    filters.folder ||
    filters.date ||
    filters.startDate ||
    filters.endDate ||
    (filters.protocols && filters.protocols.length > 0) ||
    (filters.labels && filters.labels.length > 0) ||
    (filters.qubits && filters.qubits.length > 0)
  )
}

export function notifyServerDataChanged() {
  state.serverDataVersion = (state.serverDataVersion || 0) + 1
}

// --- URL & Protocol Helpers ---
export function normalizeUrl(url) {
  return utilsNormalizeUrl(url)
}

export function getActiveServerUrl(server = state.activeServer) {
  return utilsGetActiveServerUrl(server)
}

export function getApiUrl(path) {
  return utilsGetApiUrl(path, state.activeServer)
}

export function getActiveWsUrl(path) {
  const token = getActiveAuthToken(state.activeServer)
  return utilsGetActiveWsUrl(path, state.activeServer, token)
}

export async function apiFetch(path, options = {}) {
  const url = getApiUrl(path)
  const headers = new Headers(options.headers || {})
  const token = getActiveAuthToken()
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const res = await fetch(url, { ...options, headers })
  if (res.status === 401 && state.auth?.enabled) {
    state.auth.token = null
    state.auth.user = null
    setServerAuth(state.activeServer, null, null)
    state.auth.errorMessage = 'Authentication required. Please sign in to access this instance.'
    if (typeof window !== 'undefined' && !window.location.hash.startsWith('#/servers') && !window.location.hash.startsWith('#/docs') && !window.location.hash.startsWith('#/invite') && !window.location.hash.startsWith('#/admin')) {
      window.location.hash = '#/servers'
    }
  }
  return res
}

// --- Server Management ---

export function saveStoredServers(servers) {
  localStorage.setItem(SERVERS_STORAGE_KEY, JSON.stringify(servers))
}

export async function fetchServers() {
  const server = state.servers.find(s => s.id === state.activeServer?.id) || state.servers[0]
  if (!server) {
    setActiveServer(null)
  } else if (state.activeServer?.id !== server.id) {
    await setActiveServer(server)
  } else {
    await checkActiveServerAuth(state.activeServer)
  }
  return state.servers
}

export async function ensureServersLoaded() {
  if (state.activeServer && state.servers.length > 0 && state.servers.some(s => s.id === state.activeServer?.id)) {
    return state.activeServer
  }
  await fetchServers()
  return state.activeServer
}

export function setActiveServer(server) {
  authCheckVersion++
  state.auth.checked = false
  state.auth.showLoginModal = false
  state.auth.errorMessage = ''
  if (!server) {
    state.activeServer = null
    state.auth.enabled = false
    state.auth.checked = false
    state.auth.token = null
    state.auth.user = null
    localStorage.removeItem('qibocal_active_server_id')
    return
  }
  if (getServerAuthKey(server) !== getServerAuthKey(state.activeServer)) {
    state.auth.enabled = true
    state.auth.token = null
    state.auth.user = null
  }
  state.activeServer = { ...server, url: normalizeUrl(server.url) }
  if (server.id) {
    localStorage.setItem('qibocal_active_server_id', server.id)
  }
  return checkActiveServerAuth(state.activeServer)
}

export async function addServer(urlOrObj, name = null, description = null, avatar = null, author_identities = null) {
  let payload = {}
  if (typeof urlOrObj === 'object' && urlOrObj !== null) {
    payload = { ...urlOrObj }
    payload.url = normalizeUrl(payload.url)
  } else {
    payload = {
      url: normalizeUrl(urlOrObj),
      name,
      description,
      avatar,
      author_identities
    }
  }

  const cleanUrl = payload.url
  const existing = state.servers.find(s => normalizeUrl(s.url) === cleanUrl)
  if (existing) return existing
  const id = `srv-${Math.random().toString(36).substring(2, 10)}`
  const fallbackName = payload.name || `Server ${state.servers.length + 1}`
  const created = parseClientServer({
    id,
    name: fallbackName,
    url: cleanUrl,
    description: payload.description || `Server at ${cleanUrl}`,
    avatar: payload.avatar || 'quantum-ring',
    is_default: state.servers.length === 0,
    created_at: new Date().toISOString(),
    author_identities: payload.author_identities || {},
    protocol_docs: payload.protocol_docs || {}
  })
  const servers = [...state.servers, created]
  saveStoredServers(servers)
  state.servers = servers
  if (!state.activeServer) {
    setActiveServer(created)
  }
  return created
}

export async function updateServer(id, updates) {
  const dataToSend = { ...updates }
  if (dataToSend.url) {
    dataToSend.url = normalizeUrl(dataToSend.url)
  }

  const idx = state.servers.findIndex(s => s.id === id)
  if (idx >= 0) {
    const previousUrl = normalizeUrl(state.servers[idx].url)
    const updated = parseClientServer({ ...state.servers[idx], ...dataToSend, id })
    if (state.servers.some(server => server.id !== id && normalizeUrl(server.url) === updated.url)) {
      throw new Error('A server with this address is already registered.')
    }
    const servers = [...state.servers]
    servers[idx] = updated
    saveStoredServers(servers)
    state.servers = servers
    if (normalizeUrl(updated.url) !== previousUrl) {
      setServerAuth(updated, null, null)
      localStorage.removeItem(`server_connection_${id}`)
    }
    if (state.activeServer?.id === id) {
      setActiveServer(updated)
    }
    return updated
  }
  return null
}

export async function deleteServer(id) {
  const idx = state.servers.findIndex(s => s.id === id)
  if (idx >= 0) {
    const removed = state.servers[idx]
    const servers = state.servers.filter(s => s.id !== id)
    saveStoredServers(servers)
    state.servers = servers
    setServerAuth(removed, null, null)
    localStorage.removeItem(`server_connection_${id}`)
    if (state.servers.length === 0) {
      setActiveServer(null)
    } else if (state.activeServer?.id === id) {
      setActiveServer(state.servers[0] || null)
    }
    return true
  }
  return false
}

export function exportClientState() {
  return parseClientState({
    format: 'qibocal-report-client',
    version: 1,
    servers: state.servers,
    activeServerId: state.activeServer?.id || null,
    history: state.history,
    searchState: state.searchState,
    sidebarCollapsed: state.sidebarCollapsed,
    layout: Object.fromEntries(CLIENT_LAYOUT_KEYS.map(key => [key, localStorage.getItem(key)]))
  })
}

export function importClientState(data) {
  const saved = parseClientState(data)
  const active = saved.servers.find(server => server.id === saved.activeServerId) || null
  const changes = [
    [localStorage, SERVERS_STORAGE_KEY, JSON.stringify(saved.servers)],
    [localStorage, 'qibocal_active_server_id', saved.activeServerId],
    [localStorage, 'qibocal_report_history', JSON.stringify(saved.history)],
    [localStorage, 'qibocal_report_sidebar_collapsed', String(saved.sidebarCollapsed)],
    [sessionStorage, SEARCH_STATE_STORAGE_KEY, JSON.stringify(saved.searchState)],
    [localStorage, AUTH_STORAGE_KEY, null],
    ...CLIENT_LAYOUT_KEYS.map(key => [localStorage, key, saved.layout[key] ?? null]),
    ...[...new Set([...state.servers, ...saved.servers].map(server => server.id))]
      .map(id => [localStorage, `server_connection_${id}`, null])
  ]
  const previous = changes.map(([storage, key]) => storage.getItem(key))
  let applied = 0
  try {
    for (const [storage, key, value] of changes) {
      if (value === null) storage.removeItem(key)
      else storage.setItem(key, value)
      applied++
    }
  } catch (error) {
    for (let index = applied - 1; index >= 0; index--) {
      const [storage, key] = changes[index]
      if (previous[index] === null) storage.removeItem(key)
      else storage.setItem(key, previous[index])
    }
    throw error
  }

  authCheckVersion++
  clientStateVersion++
  for (const key of Object.keys(serverAuth)) delete serverAuth[key]
  state.servers = saved.servers
  state.activeServer = active
  state.history = saved.history
  state.searchState = saved.searchState
  state.sidebarCollapsed = saved.sidebarCollapsed
  Object.assign(state.auth, {
    enabled: Boolean(active), checked: false, token: null, user: null,
    showLoginModal: false, showRegisterModal: false, registerData: null, errorMessage: ''
  })
  state.currentReportId = null
  state.currentReportData = null
  state.pendingFilter = null
  state.loading = false
  state.error = null
  notifyServerDataChanged()
}

// --- Report History Management (Scoped to Active Server) ---
function canonicalUrl(url) {
  if (!url) return ''
  return normalizeUrl(url)
    .replace(/^https?:\/\/localhost\b/i, 'http://127.0.0.1')
    .replace(/^https?:\/\/127\.0\.0\.1\b/i, 'http://127.0.0.1')
}

export function isReportOnServer(historyItem, server = state.activeServer) {
  if (!historyItem) return false
  if (!server) return true

  const serverUrl = server.url ? normalizeUrl(server.url) : ''
  const serverId = server.id || null
  const itemUrl = historyItem.server_url ? normalizeUrl(historyItem.server_url) : ''
  const itemId = historyItem.server_id || null

  // 1. Explicit server ID match
  if (serverId && itemId && serverId === itemId) return true

  // 2. Explicit server URL match (canonicalized for localhost / 127.0.0.1 equivalence)
  if (serverUrl && itemUrl) {
    if (canonicalUrl(serverUrl) === canonicalUrl(itemUrl)) return true
  }

  // 3. Fallback for legacy history entries without server association
  if (!itemId && !itemUrl) {
    if (server.is_default || serverId === 'srv-local' || canonicalUrl(serverUrl).includes('127.0.0.1:8000')) {
      return true
    }
    if (state.servers.length <= 1) {
      return true
    }
  }

  return false
}

export const activeServerHistory = computed(() => {
  return state.history
    .filter(h => isReportOnServer(h, state.activeServer))
    .slice(0, 15)
})

export function addToHistory(report, server = state.activeServer) {
  if (!report || !report.id) return
  const srv = server || state.activeServer || (state.servers.length > 0 ? state.servers[0] : null)
  const activeUrl = srv?.url ? normalizeUrl(srv.url) : ''
  const activeId = srv?.id || null

  const newEntry = {
    id: report.id,
    platform: report.platform,
    date: report.date,
    tags: report.tags || report.labels || [],
    opened_at: new Date().toISOString(),
    server_id: activeId,
    server_url: activeUrl
  }

  // Filter out duplicate of this report on the same server
  state.history = [
    newEntry,
    ...state.history.filter(h => {
      if (h.id !== report.id) return true
      return !isReportOnServer(h, srv)
    })
  ].slice(0, 100)

  try {
    localStorage.setItem('qibocal_report_history', JSON.stringify(state.history))
  } catch (e) {
    console.error('Failed to save history to localStorage', e)
  }
}

export function removeFromHistory(reportIds, server = state.activeServer) {
  const ids = Array.isArray(reportIds) ? reportIds : [reportIds]
  if (ids.length === 0) return
  state.history = state.history.filter(h => {
    if (!ids.includes(h.id)) return true
    if (server && !isReportOnServer(h, server)) return true
    return false
  })
  try {
    localStorage.setItem('qibocal_report_history', JSON.stringify(state.history))
  } catch (e) {
    console.error('Failed to update history in localStorage', e)
  }
}

export function clearHistory(server = state.activeServer) {
  if (server) {
    state.history = state.history.filter(h => !isReportOnServer(h, server))
  } else {
    state.history = []
  }
  try {
    localStorage.setItem('qibocal_report_history', JSON.stringify(state.history))
  } catch (e) {
    console.error('Failed to clear history in localStorage', e)
  }
}

// --- Author Resolution ---
export function resolveAuthor(author, server = state.activeServer) {
  if (!author || author === 'Unknown') return author || 'Unknown'
  const identities = server?.author_identities
  if (!identities || typeof identities !== 'object') return author
  const clean = author.trim().toLowerCase()
  for (const [canonical, aliases] of Object.entries(identities)) {
    if (canonical.trim().toLowerCase() === clean) return canonical
    if (
      Array.isArray(aliases) &&
      aliases.some(a => a && a.trim().toLowerCase() === clean)
    ) {
      return canonical
    }
  }
  return author
}
