import { reactive } from 'vue'

const savedHistory = localStorage.getItem('qibocal_report_history')
const initialHistory = savedHistory ? JSON.parse(savedHistory) : []

export const state = reactive({
  servers: [],
  activeServer: null,
  history: initialHistory,
  currentReportId: null,
  currentReportData: null,
  sidebarCollapsed: false,
  loading: false,
  error: null
})

export function normalizeUrl(url) {
  if (!url) return ''
  let clean = url.trim().replace(/\/+$/, '')
  if (!clean.startsWith('http://') && !clean.startsWith('https://')) {
    clean = `http://${clean}`
  }
  return clean
}

export function getActiveServerUrl() {
  if (state.activeServer?.url) {
    return normalizeUrl(state.activeServer.url)
  }
  return ''
}

export function getApiUrl(path) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  const base = getActiveServerUrl()
  if (base) {
    return `${base}${cleanPath}`
  }
  return cleanPath
}

export function getActiveWsUrl(path) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  const serverUrl = getActiveServerUrl()
  if (serverUrl) {
    const wsBase = serverUrl.replace(/^http:\/\//i, 'ws://').replace(/^https:\/\//i, 'wss://')
    return `${wsBase}${cleanPath}`
  }
  const isHttps = typeof window !== 'undefined' && window.location?.protocol === 'https:'
  const wsProto = isHttps ? 'wss:' : 'ws:'
  const host = (typeof window !== 'undefined' && window.location?.host) || '127.0.0.1:8000'
  return `${wsProto}//${host}${cleanPath}`
}

export async function apiFetch(path, options = {}) {
  const url = getApiUrl(path)
  return fetch(url, options)
}

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

export function addToHistory(report) {
  if (!report || !report.id) return
  // filter out existing entry with same id
  state.history = [
    {
      id: report.id,
      platform: report.platform,
      date: report.date,
      tags: report.tags || report.labels || [],
      opened_at: new Date().toISOString()
    },
    ...state.history.filter(h => h.id !== report.id)
  ].slice(0, 15) // Keep last 15 reports
  localStorage.setItem('qibocal_report_history', JSON.stringify(state.history))
}

export function clearHistory() {
  state.history = []
  localStorage.removeItem('qibocal_report_history')
}

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
