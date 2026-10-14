import { normalizeUrl } from '../../../frontend/src/utils/url.js'

export const DASHBOARD_SERVERS_KEY = 'qibocal_report_servers'
export const DASHBOARD_ACTIVE_KEY = 'qibocal_active_server_id'

export { normalizeUrl }

/** A host, optionally bracketed for IPv6, optionally followed by a port. */
const ADDRESS = /^https?:\/\/(\[[0-9a-fA-F:]+\]|[^\s/?#:]+)(:\d+)?([/?#]|$)/

/**
 * The frontend normalisation, refusing what it would turn into a bare scheme.
 *
 * `normalizeUrl('')` answers `'http://'`, which is enough for the dashboard's
 * own form but would let an address nobody can reach into `servers.json`.
 */
export function serverUrl(value) {
  const url = normalizeUrl(typeof value === 'string' ? value : '')
  return ADDRESS.test(url) ? url : ''
}

function stringMap(value, arrays) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return {}
  return Object.fromEntries(
    Object.entries(value)
      .filter(([, entry]) => arrays
        ? Array.isArray(entry) && entry.every(item => typeof item === 'string')
        : typeof entry === 'string')
      .map(([key, entry]) => [key, arrays ? [...entry] : entry])
  )
}

/**
 * Project a `servers.json` entry onto the schema the dashboard stores in the
 * browser, so both halves of the application describe the same instance.
 */
export function toDashboardServer(server, fallbackIndex = 0) {
  const url = serverUrl(server?.url)
  if (!url) return null
  return {
    id: typeof server?.id === 'string' && server.id ? server.id : `srv-local-${fallbackIndex}`,
    name: typeof server?.name === 'string' && server.name ? server.name : url,
    url,
    description: typeof server?.description === 'string' ? server.description : `Server at ${url}`,
    avatar: typeof server?.avatar === 'string' && server.avatar ? server.avatar : 'quantum-ring',
    created_at: typeof server?.created_at === 'string' ? server.created_at : new Date().toISOString(),
    author_identities: stringMap(server?.author_identities, true),
    protocol_docs: stringMap(server?.protocol_docs, false)
  }
}

/**
 * Merge the configured servers into the dashboard list, matching on address.
 *
 * Entries registered from the dashboard itself are preserved: the launcher
 * only adds what the command line knows about, and refreshes the labels of
 * instances it already shares.
 */
export function mergeDashboardServers(configured, existing = []) {
  const merged = Array.isArray(existing) ? existing.filter(server => serverUrl(server?.url)) : []
  const byUrl = new Map(merged.map((server, index) => [serverUrl(server.url), index]))

  ;(Array.isArray(configured) ? configured : []).forEach((server, index) => {
    const candidate = toDashboardServer(server, index)
    if (!candidate) return
    const position = byUrl.get(candidate.url)
    if (position === undefined) {
      byUrl.set(candidate.url, merged.length)
      merged.push(candidate)
      return
    }
    const current = merged[position]
    merged[position] = {
      ...candidate,
      id: current.id || candidate.id,
      author_identities: Object.keys(current.author_identities ?? {}).length
        ? current.author_identities
        : candidate.author_identities,
      protocol_docs: Object.keys(current.protocol_docs ?? {}).length
        ? current.protocol_docs
        : candidate.protocol_docs
    }
  })

  return merged.map((server, index) => ({
    ...server,
    is_default: index === 0
  }))
}

function readStored(storage, key) {
  try {
    const raw = storage.getItem(key)
    const parsed = raw ? JSON.parse(raw) : null
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

/**
 * Publish the configured servers to the bundled dashboard and select one.
 *
 * Both pages share a single origin inside the application window, so the
 * dashboard simply finds the instances the launcher started.
 */
export function syncDashboardServers(configured, { storage, preferredUrl = null } = {}) {
  const store = storage ?? (typeof localStorage === 'undefined' ? null : localStorage)
  const servers = mergeDashboardServers(configured, store ? readStored(store, DASHBOARD_SERVERS_KEY) : [])
  if (!store) return servers

  store.setItem(DASHBOARD_SERVERS_KEY, JSON.stringify(servers))
  const target = preferredUrl ? serverUrl(preferredUrl) : null
  const selected = (target && servers.find(server => server.url === target)) ||
    servers.find(server => server.id === store.getItem(DASHBOARD_ACTIVE_KEY)) ||
    servers[0]
  if (selected) {
    store.setItem(DASHBOARD_ACTIVE_KEY, selected.id)
  } else {
    store.removeItem(DASHBOARD_ACTIVE_KEY)
  }
  return servers
}
