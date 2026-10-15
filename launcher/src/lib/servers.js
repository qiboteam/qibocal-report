import { normalizeUrl } from '../../../frontend/src/utils/url.js'
import { ADJECTIVES, SCIENTISTS, generateServerName } from '../../../frontend/src/utils/names.js'

export { ADJECTIVES, SCIENTISTS }

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

function quote(value) {
  return /^[\w@%+=:,./-]+$/.test(value) ? value : `'${String(value).replace(/'/g, "'\\''")}'`
}

/**
 * The command the launcher runs for a set of start options.
 *
 * It is both what the form shows under the button and, word for word, what
 * `process.rs::start_server` assembles — the two cannot drift while this is the
 * only place that spells the flags out.
 */
export function serverCommand(options = {}) {
  const mode = options.mode || 'server'
  const ssh = typeof options.ssh === 'string' ? options.ssh.trim() : ''
  const name = typeof options.name === 'string' ? options.name.trim() : ''
  const directory = typeof options.directory === 'string' ? options.directory.trim() : ''
  const parts = ['qibocal', 'report', mode]
  // No directory is the shared one, found and created where the server runs.
  if (mode !== 'client' && directory) parts.push(directory)
  if (!ssh) {
    parts.push('--host', options.host || 'localhost', '--port', String(options.port ?? 8000))
  }
  if (mode !== 'client') {
    parts.push(options.auth ? '--auth' : '--no-auth')
    if (name) parts.push('--name', name)
    if (options.register === false) parts.push('--no-register')
  }
  if (mode === 'dev') parts.push('--frontend-port', String(options.frontendPort ?? 5173))
  // Without a destination the rest of the remote options mean nothing, and
  // the command line refuses them: they go together or not at all.
  if (ssh) {
    for (const [flag, value] of [
      ['--ssh', ssh],
      ['--workdir', options.workdir],
      ['--venv', options.venv],
      ['--install', options.install]
    ]) {
      const text = typeof value === 'string' ? value.trim() : ''
      if (text) parts.push(flag, text)
    }
    if (options.timeout) parts.push('--timeout', String(options.timeout))
  }
  return parts.map(quote).join(' ')
}

/** Where the shared reports live, as the forms spell it out. */
export const SHARED_DIRECTORY = '~/.local/share/qibocal/reports (or $XDG_DATA_HOME/qibocal/reports)'

/** Where a server runs: the choice that decides which fields make sense. */
export const PLACES = [
  { value: 'local', label: 'This machine', help: 'Run qibocal here.' },
  { value: 'ssh', label: 'Another machine', help: 'Reach a host over SSH, prepare an environment there, and tunnel the server back.' },
  { value: 'reachable', label: 'Already running', help: 'Register an address, starting nothing.' }
]

/** A server form, every field at its default. */
export function blankForm() {
  return {
    name: '',
    description: '',
    mode: 'server',
    directory: '',
    host: 'localhost',
    port: 8000,
    auth: false,
    frontendPort: 5173,
    ssh: '',
    venv: '',
    workdir: '',
    install: '',
    url: ''
  }
}

/**
 * The form filled in from start options — remembered, or the default ones
 * for a registered server — and from the entry itself: what "Edit" opens
 * on, and what the system menu's "start again" prefills. Options that are
 * absent mean a server the launcher does not start.
 */
export function formFrom(options, server = null) {
  const form = blankForm()
  form.name = server?.name || options?.name || ''
  form.description = server?.description || ''
  form.url = server?.url || ''
  if (!options) return { where: 'reachable', form }
  Object.assign(form, {
    mode: options.mode || 'server',
    directory: options.directory || '',
    host: options.host || 'localhost',
    port: options.port || 8000,
    auth: Boolean(options.auth),
    frontendPort: options.frontendPort || 5173,
    ssh: options.ssh || '',
    venv: options.venv || '',
    workdir: options.workdir || '',
    install: options.install || ''
  })
  return { where: options.ssh ? 'ssh' : 'local', form }
}

/**
 * What is wrong with a form, by field; nothing when it can be submitted.
 * A registered entry needs an address whatever the place.
 */
export function formProblems(where, form, { entry = false } = {}) {
  const found = {}
  if (where === 'ssh' && !String(form.ssh || '').trim()) {
    found.ssh = 'Name the machine to reach, as ssh would.'
  }
  const url = String(form.url || '')
  if ((entry || (where === 'reachable' && url)) && !serverUrl(url)) {
    found.url = 'Enter the address of the report server.'
  }
  const port = Number(form.port)
  if (where === 'local' && (!Number.isInteger(port) || port < 1 || port > 65535)) {
    found.port = 'Enter a port between 1 and 65535.'
  }
  return found
}

/**
 * The start options a form describes: exactly what `start_server` receives,
 * and what the command preview shows. Nothing for a server the launcher
 * does not start.
 */
export function launchFrom(where, form, { name = null, register = false } = {}) {
  if (where === 'reachable') return null
  const away = where === 'ssh'
  const mode = away ? 'server' : form.mode
  const text = value => String(value || '').trim() || null
  return {
    mode,
    name: text(form.name) || name,
    register,
    directory: mode === 'client' ? null : text(form.directory),
    host: text(form.host) || 'localhost',
    port: Number(form.port),
    auth: Boolean(form.auth),
    frontendPort: mode === 'dev' ? Number(form.frontendPort) : null,
    ssh: away ? text(form.ssh) : null,
    venv: away ? text(form.venv) : null,
    workdir: away ? text(form.workdir) : null,
    install: away ? text(form.install) : null
  }
}

/** The hosts a server on this machine can bind: the ones a local address names. */
const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1', '::1', '[::1]', '0.0.0.0'])

/**
 * The addresses under which a launch may have been remembered: the same
 * server is spoken of as localhost and as 127.0.0.1 by different hands.
 */
export function launchKeys(url) {
  const key = serverUrl(url)
  if (!key) return []
  const keys = [key]
  for (const [from, to] of [['localhost', '127.0.0.1'], ['127.0.0.1', 'localhost']]) {
    const alias = key.replace(new RegExp(`^(https?://)${from.replace('.', '\\.')}(?=[:/]|$)`), `$1${to}`)
    if (alias !== key) keys.push(alias)
  }
  return keys
}

/**
 * How to start a registered server the launcher has never started: on this
 * machine, at the address it is registered under, serving the shared
 * directory. Nothing, when the address is not this machine's.
 */
export function defaultLaunch(server) {
  const url = serverUrl(server?.url)
  if (!url) return null
  let parsed
  try {
    parsed = new URL(url)
  } catch {
    return null
  }
  if (!LOCAL_HOSTS.has(parsed.hostname)) return null
  return {
    mode: 'server',
    name: typeof server.name === 'string' && server.name ? server.name : null,
    register: true,
    directory: null,
    host: parsed.hostname,
    port: Number(parsed.port) || (parsed.protocol === 'https:' ? 443 : 80),
    auth: false,
    frontendPort: null,
    ssh: null,
    venv: null,
    workdir: null,
    install: null
  }
}

/**
 * A name for the next server: an adjective and a scientist, as the command
 * line and the dashboard name theirs, avoiding the ones already in use.
 */
export function suggestServerName(taken = [], random = Math.random) {
  return generateServerName(taken, random)
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
