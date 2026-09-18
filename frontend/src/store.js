import { reactive, computed } from 'vue'
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

// --- Search State Persistence (Session Storage) ---
const SEARCH_STATE_STORAGE_KEY = 'qibocal_report_search_state'

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
  servers: [],
  activeServer: null,
  history: initialHistory,
  currentReportId: null,
  currentReportData: null,
  sidebarCollapsed: false,
  loading: false,
  error: null,
  serverDataVersion: 0,
  pendingFilter: null,
  searchState: loadSavedSearchState()
})

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

export function getActiveServerUrl() {
  return utilsGetActiveServerUrl(state.activeServer)
}

export function getApiUrl(path) {
  return utilsGetApiUrl(path, state.activeServer)
}

export function getActiveWsUrl(path) {
  return utilsGetActiveWsUrl(path, state.activeServer)
}

export async function apiFetch(path, options = {}) {
  const url = getApiUrl(path)
  return fetch(url, options)
}

// --- Server Management ---
let serversPromise = null

export function fetchServers() {
  if (!serversPromise) {
    serversPromise = (async () => {
      try {
        const res = await fetch('/api/servers')
        if (res.ok) {
          const data = await res.json()
          state.servers = data
          const savedActiveId = localStorage.getItem('qibocal_active_server_id')
          const found = data.find(s => s.id === savedActiveId)
          if (found) {
            state.activeServer = found
          } else if (!state.activeServer && data.length > 0) {
            state.activeServer = data[0]
          } else if (state.activeServer) {
            const current = data.find(s => s.id === state.activeServer.id)
            if (current) state.activeServer = current
          }
          if (state.activeServer?.id) {
            localStorage.setItem('qibocal_active_server_id', state.activeServer.id)
          }
        }
      } catch (err) {
        console.error('Failed to fetch servers', err)
      } finally {
        serversPromise = null
      }
    })()
  }
  return serversPromise
}

export async function ensureServersLoaded() {
  if (state.activeServer && state.servers.length > 0) {
    return state.activeServer
  }
  await fetchServers()
  return state.activeServer
}

export function setActiveServer(server) {
  if (!server) {
    state.activeServer = null
    localStorage.removeItem('qibocal_active_server_id')
    return
  }
  state.activeServer = { ...server, url: normalizeUrl(server.url) }
  if (server.id) {
    localStorage.setItem('qibocal_active_server_id', server.id)
  }
}

export async function addServer(urlOrObj, name = null, description = null, avatar = null, author_identities = null) {
  try {
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
    const res = await fetch('/api/servers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (res.ok) {
      const created = await res.json()
      await fetchServers()
      return created
    }
  } catch (err) {
    console.error('Failed to add server', err)
  }
  return null
}

export async function updateServer(id, updates) {
  try {
    const dataToSend = { ...updates }
    if (dataToSend.url) {
      dataToSend.url = normalizeUrl(dataToSend.url)
    }
    const res = await fetch(`/api/servers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dataToSend)
    })
    if (res.ok) {
      const updated = await res.json()
      await fetchServers()
      if (state.activeServer?.id === id) {
        setActiveServer(updated)
      }
      return updated
    }
  } catch (err) {
    console.error('Failed to update server', err)
  }
  return null
}

export async function deleteServer(id) {
  try {
    const res = await fetch(`/api/servers/${id}`, { method: 'DELETE' })
    if (res.ok) {
      await fetchServers()
      if (state.activeServer?.id === id) {
        setActiveServer(state.servers[0] || null)
      }
      return true
    }
  } catch (err) {
    console.error('Failed to delete server', err)
  }
  return false
}

export async function persistServersConfig() {
  try {
    const res = await fetch('/api/servers/save', { method: 'POST' })
    if (res.ok) {
      return await res.json()
    }
  } catch (err) {
    console.error('Failed to save config', err)
  }
  return null
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
