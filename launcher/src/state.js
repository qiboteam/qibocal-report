import { reactive, computed } from 'vue'
import { desktop, isDesktop, subscribe } from './bridge.js'
import { syncDashboardServers, serverUrl } from './lib/servers.js'

export const LOG_EVENT = 'launcher://log'
export const PROCESS_EVENT = 'launcher://process'

export const state = reactive({
  ready: false,
  environment: null,
  servers: [],
  notebooks: {},
  processes: [],
  configEntries: [],
  preferences: {},
  logs: {},
  notice: null,
  error: null
})

export const hasQibocal = computed(() => Boolean(state.environment?.executable))

/** Whether the launcher is installing or updating its own Qibocal right now. */
export const installing = computed(() =>
  state.processes.some(process => process.kind === 'setup' && process.status === 'running')
)

export function notify(message) {
  state.error = null
  state.notice = message
}

export function fail(error) {
  state.notice = null
  state.error = typeof error === 'string' ? error : (error?.message || String(error))
}

export function dismiss() {
  state.notice = null
  state.error = null
}

/** Run an action, surfacing its failure in the banner instead of the console. */
export async function attempt(action, success = null) {
  try {
    const result = await action()
    if (success) notify(typeof success === 'function' ? success(result) : success)
    return result
  } catch (error) {
    fail(error)
    return undefined
  }
}

async function load(loader, fallback) {
  try {
    return await loader()
  } catch {
    return fallback
  }
}

export async function refreshEnvironment() {
  state.environment = await load(desktop.environment, null)
  return state.environment
}

export async function refreshServers() {
  state.servers = await load(desktop.listServers, [])
  return state.servers
}

export async function refreshNotebooks() {
  state.notebooks = await load(desktop.listNotebooks, {})
  return state.notebooks
}

export async function refreshProcesses() {
  state.processes = await load(desktop.processes, [])
  return state.processes
}

export async function refreshConfigEntries() {
  state.configEntries = await load(desktop.configEntries, [])
  return state.configEntries
}

export async function refreshPreferences() {
  state.preferences = await load(desktop.preferences, {})
  return state.preferences
}

/**
 * Remember how a server was started, so the same instance can be brought up
 * again from the system menu without filling the form a second time.
 */
export async function rememberLaunch(url, options) {
  const key = serverUrl(url)
  if (!key) return
  const launches = { ...(state.preferences.launches || {}), [key]: options }
  state.preferences = await desktop.savePreferences({ ...state.preferences, launches })
}

export function recallLaunch(url) {
  const key = serverUrl(url)
  return (key && state.preferences.launches?.[key]) || null
}

/**
 * Launches still waiting for an address, by process.
 *
 * A server started over SSH is reached through a tunnel whose local port is
 * only known once the command line prints it, so its options are kept here
 * until `mergeProcess` sees that address go by.
 */
const pending = new Map()

/** Start a report server and keep its options for the next time. */
export async function startServer(options, { url = null } = {}) {
  const info = await desktop.startServer(options)
  mergeProcess(info)
  if (!url && !info.url && options.ssh) {
    pending.set(info.id, options)
    return info
  }
  const address = url || info.url || `http://${options.host || '127.0.0.1'}:${options.port}`
  await rememberLaunch(address, options)
  return info
}

export function processById(id) {
  return state.processes.find(process => process.id === id) || null
}

/** The report servers the launcher is running right now, address known. */
export function runningServers() {
  return state.processes.filter(
    process => process.kind === 'server' && process.status === 'running' && serverUrl(process.url)
  )
}

/** Running servers that are in no configuration file: started for a look. */
export function unregisteredServers() {
  const registered = new Set(state.servers.map(server => serverUrl(server.url)))
  return runningServers().filter(process => !registered.has(serverUrl(process.url)))
}

/** Create the launcher's own Qibocal environment, or update it. */
export async function installQibocal(upgrade = false) {
  const info = await desktop.installQibocal(upgrade)
  mergeProcess(info)
  return info
}

function mergeProcess(info) {
  const index = state.processes.findIndex(process => process.id === info.id)
  if (index >= 0) state.processes[index] = info
  else state.processes.push(info)

  // An installation that ended changed what the launcher can find.
  if (info.kind === 'setup' && info.status !== 'running') refreshEnvironment()

  const waiting = pending.get(info.id)
  if (!waiting) return
  if (info.url) {
    pending.delete(info.id)
    rememberLaunch(info.url, waiting)
  } else if (info.status !== 'running') {
    pending.delete(info.id)
  }
}

export async function loadLog(id) {
  const lines = await load(() => desktop.processLog(id), [])
  state.logs[id] = lines
  return lines
}

/** Connect the native events once, when the launcher page starts. */
export async function initialize() {
  if (state.ready) return
  state.ready = true
  if (!isDesktop) return

  await subscribe(LOG_EVENT, payload => {
    const lines = state.logs[payload.id] || (state.logs[payload.id] = [])
    lines.push(payload.line)
    if (lines.length > 2000) lines.splice(0, lines.length - 2000)
  })
  await subscribe(PROCESS_EVENT, mergeProcess)

  await Promise.all([
    refreshEnvironment(),
    refreshServers(),
    refreshNotebooks(),
    refreshProcesses(),
    refreshConfigEntries(),
    refreshPreferences()
  ])
  await installIfMissing()
}

/**
 * Nothing to click on first run: when no Qibocal is found and a Python is,
 * the launcher installs its own in the background. Once per session — a
 * failed attempt is left in Running for the user to read, not retried.
 */
let offered = false
export async function installIfMissing() {
  if (offered || !isDesktop) return
  const environment = state.environment
  if (!environment || environment.executable || !environment.python || installing.value) return
  offered = true
  try {
    await installQibocal(false)
    notify('No Qibocal was found: installing it now. The progress is in Running.')
  } catch (error) {
    fail(error)
  }
}

/**
 * Hand the configured servers over to the bundled dashboard and open it.
 *
 * Both pages live in the same window, hence in the same origin, so the
 * dashboard reads the instances the launcher just registered.
 */
export function openDashboard(preferredUrl = null) {
  syncDashboardServers(state.servers, { preferredUrl, running: runningServers() })
  const target = new URL('dashboard.html', window.location.href)
  if (preferredUrl) target.hash = '#/dashboard'
  window.location.href = target.href
}

/** Register a server address in `servers.json`, without duplicating it. */
export async function registerServer(server) {
  const url = serverUrl(server.url)
  if (!url) throw new Error('Enter the address of the report server.')
  const servers = [...state.servers]
  const index = servers.findIndex(entry => serverUrl(entry.url) === url)
  const entry = {
    id: servers[index]?.id || `srv-${Math.random().toString(36).slice(2, 10)}`,
    created_at: servers[index]?.created_at || new Date().toISOString(),
    avatar: 'quantum-ring',
    ...servers[index],
    ...server,
    url
  }
  if (index >= 0) servers[index] = entry
  else servers.push(entry)
  state.servers = await desktop.saveServers(servers)
  return entry
}

export async function forgetServer(id) {
  state.servers = await desktop.saveServers(state.servers.filter(server => server.id !== id))
}
