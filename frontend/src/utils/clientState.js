import { normalizeUrl } from './url.js'

export const CLIENT_LAYOUT_KEYS = [
  'qibocal_report_table_columns_v1',
  'qibocal_sidebar_width',
  'qibocal_sidebar_top_height',
  'qibocal_sidebar_middle_height'
]

function requireValue(condition, field) {
  if (!condition) throw new Error(`Invalid client state: ${field}.`)
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function string(value, field) {
  requireValue(typeof value === 'string', field)
  return value
}

function nullableString(value, field) {
  return value == null ? null : string(value, field)
}

function strings(value, field) {
  requireValue(Array.isArray(value) && value.every(item => typeof item === 'string'), field)
  return [...value]
}

function stringMap(value, field, arrays = false) {
  requireValue(isObject(value), field)
  return Object.fromEntries(Object.entries(value).map(([key, entry]) => [
    key, arrays ? strings(entry, field) : string(entry, field)
  ]))
}

export function parseClientServer(server) {
  requireValue(isObject(server), 'server')
  const id = string(server.id, 'server ID')
  requireValue(id.length > 0, 'empty server ID')
  const url = normalizeUrl(string(server.url, 'server URL'))
  const parsedUrl = new URL(url)
  requireValue(['http:', 'https:'].includes(parsedUrl.protocol) &&
    !parsedUrl.username && !parsedUrl.password, 'server URL')
  const result = { id, name: string(server.name, 'server name'), url }
  for (const key of ['description', 'avatar', 'created_at']) {
    if (server[key] != null) result[key] = string(server[key], `server ${key}`)
  }
  if (server.is_default != null) {
    requireValue(typeof server.is_default === 'boolean', 'server default flag')
    result.is_default = server.is_default
  }
  result.author_identities = stringMap(server.author_identities ?? {}, 'author identities', true)
  result.protocol_docs = stringMap(server.protocol_docs ?? {}, 'protocol documentation')
  return result
}

// Project onto known fields so credentials and arbitrary storage keys cannot be imported or exported.
export function parseClientState(data) {
  requireValue(isObject(data) && data.format === 'qibocal-report-client' && data.version === 1,
    'unsupported file format or version')
  requireValue(Array.isArray(data.servers), 'server list')
  const servers = data.servers.map(parseClientServer)
  const ids = new Set(servers.map(server => server.id))
  const urls = new Set(servers.map(server => server.url))
  requireValue(ids.size === servers.length && urls.size === servers.length, 'duplicate servers')
  const activeServerId = nullableString(data.activeServerId, 'active server')
  requireValue(activeServerId === null || ids.has(activeServerId), 'unknown active server')
  requireValue(Array.isArray(data.history), 'report history')
  const history = data.history.map(entry => {
    requireValue(isObject(entry), 'history entry')
    const result = { id: string(entry.id, 'report ID'), tags: strings(entry.tags ?? [], 'report tags') }
    for (const key of ['platform', 'date', 'opened_at', 'server_id', 'server_url']) {
      if (entry[key] !== undefined) result[key] = nullableString(entry[key], `history ${key}`)
    }
    return result
  })
  requireValue(isObject(data.searchState) && isObject(data.searchState.filters), 'search settings')
  const searchState = { serverId: nullableString(data.searchState.serverId, 'search server'), filters: {} }
  for (const key of ['q', 'author', 'platform', 'folder', 'date', 'startDate', 'endDate', 'sort_by']) {
    searchState.filters[key] = string(data.searchState.filters[key], `filter ${key}`)
  }
  for (const key of ['protocols', 'labels', 'qubits']) {
    searchState.filters[key] = strings(data.searchState.filters[key], `filter ${key}`)
  }
  for (const key of ['currentPage', 'pageSize']) {
    requireValue(Number.isSafeInteger(data.searchState[key]) && data.searchState[key] > 0, key)
    searchState[key] = data.searchState[key]
  }
  requireValue(typeof data.sidebarCollapsed === 'boolean', 'sidebar preference')
  requireValue(isObject(data.layout), 'layout preferences')
  const layout = {}
  for (const key of CLIENT_LAYOUT_KEYS) {
    if (data.layout[key] == null) continue
    const raw = string(data.layout[key], `layout ${key}`)
    if (key === 'qibocal_report_table_columns_v1') {
      const widths = JSON.parse(raw)
      requireValue(isObject(widths) && Object.values(widths).every(width =>
        typeof width === 'number' && Number.isFinite(width) && width > 0), 'column widths')
      layout[key] = JSON.stringify(widths)
    } else {
      requireValue(Number.isFinite(Number(raw)) && Number(raw) > 0, 'sidebar dimensions')
      layout[key] = raw
    }
  }
  return {
    format: 'qibocal-report-client',
    version: 1,
    servers,
    activeServerId,
    history,
    searchState,
    sidebarCollapsed: data.sidebarCollapsed,
    layout
  }
}
