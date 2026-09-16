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

export async function fetchServers() {
  try {
    const res = await fetch('/api/servers')
    if (res.ok) {
      const data = await res.json()
      state.servers = data
      if (!state.activeServer && data.length > 0) {
        // default to active server from localStorage or first
        const savedActiveId = localStorage.getItem('qibocal_active_server_id')
        const found = data.find(s => s.id === savedActiveId)
        state.activeServer = found || data[0]
      }
    }
  } catch (err) {
    console.error('Failed to fetch servers', err)
  }
}

export function setActiveServer(server) {
  state.activeServer = server
  if (server?.id) {
    localStorage.setItem('qibocal_active_server_id', server.id)
  }
}

export async function addServer(url, name = null, description = null, avatar = null) {
  try {
    const res = await fetch('/api/servers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, name, description, avatar })
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
    const res = await fetch(`/api/servers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    })
    if (res.ok) {
      const updated = await res.json()
      await fetchServers()
      if (state.activeServer?.id === id) {
        state.activeServer = updated
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
        state.activeServer = state.servers[0] || null
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
      title: report.title,
      platform: report.platform,
      date: report.date,
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
