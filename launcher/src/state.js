import { reactive, computed } from 'vue'
import { desktop, isDesktop, subscribe } from './bridge.js'
import { syncDashboardServers, serverUrl } from './lib/servers.js'

export const LOG_EVENT = 'launcher://log'
export const PROCESS_EVENT = 'launcher://process'

/** How long a message stays in the status bar, by kind. */
const MESSAGE_TTL = { info: 6000, error: 15000 }

export const state = reactive({
  ready: false,
  environment: null,
  servers: [],
  notebooks: {},
  processes: [],
  configEntries: [],
  preferences: {},
  logs: {},
  /** The latest thing said, shown in the status bar until it fades; null when quiet. */
  message: null,
  /** Everything said so far, newest first, each until dismissed. */
  notifications: []
})

export const hasQibocal = computed(() => Boolean(state.environment?.executable))

/** Whether the launcher is installing or updating its own qibocal-report right now. */
export const installing = computed(() =>
  state.processes.some(process => process.kind === 'setup' && process.status === 'running')
)

// --- Messages ---------------------------------------------------------------

/** How many notifications are kept, newest first. */
const NOTIFICATION_LIMIT = 50

let messageTimer = null
let counter = 0

/**
 * Say something in the status bar, and let it fade on its own.
 *
 * Messages never interrupt: the latest shows in the bottom-right corner
 * until it fades, and all of them stay in the list behind the counter
 * next to it, each until dismissed. Nothing moves on the page.
 */
function say(text, kind) {
  counter += 1
  const entry = { id: counter, text, kind, at: Date.now() }
  state.notifications.unshift(entry)
  if (state.notifications.length > NOTIFICATION_LIMIT) state.notifications.length = NOTIFICATION_LIMIT
  clearTimeout(messageTimer)
  state.message = entry
  messageTimer = setTimeout(() => {
    if (state.message?.id === entry.id) state.message = null
  }, MESSAGE_TTL[kind])
}

export function notify(message) {
  say(message, 'info')
}

export function fail(error) {
  say(typeof error === 'string' ? error : (error?.message || String(error)), 'error')
}

export function dismissNotification(id) {
  state.notifications = state.notifications.filter(entry => entry.id !== id)
  if (state.message?.id === id) state.message = null
}

export function dismiss() {
  clearTimeout(messageTimer)
  state.message = null
  state.notifications = []
}

/** Run an action, surfacing its failure in the status bar instead of the console. */
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

// --- Loading ----------------------------------------------------------------

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

// --- The command line, installed when first needed ---------------------------

/** Create the launcher's own qibocal-report environment, or update it. */
export async function installQibocal(upgrade = false) {
  const info = await desktop.installQibocal(upgrade)
  mergeProcess(info)
  return info
}

/** Whoever is waiting for the command line to exist: settled by `mergeProcess`. */
const awaitingSetup = []

/**
 * Make sure the command line is there, installing it if it is not.
 *
 * Nothing is installed on opening the application: the first server,
 * notebook or invitation that needs qibocal-report starts the installation,
 * and goes on by itself once it is done — with a word in the status bar
 * meanwhile, and the output in Running.
 */
export async function ensureQibocal() {
  if (hasQibocal.value) return
  if (!state.environment?.python) {
    throw new Error('No Python 3.10 or newer was found to install qibocal-report with; see Configuration.')
  }
  if (!installing.value) await installQibocal(false)
  await new Promise((resolve, reject) => awaitingSetup.push({ resolve, reject }))
}

/** Run something that needs the command line, installing it first if needed. */
export async function withQibocal(action) {
  await ensureQibocal()
  return action()
}

async function settleSetup(info) {
  await refreshEnvironment()
  const waiting = awaitingSetup.splice(0)
  if (hasQibocal.value) {
    if (waiting.length) notify('qibocal-report is installed; carrying on.')
    waiting.forEach(entry => entry.resolve())
    return
  }
  const reason = info.status === 'failed'
    ? 'The installation of qibocal-report failed; its output is in Running.'
    : 'qibocal-report is still missing after the installation; see Running.'
  waiting.forEach(entry => entry.reject(new Error(reason)))
  if (!waiting.length) fail(reason)
}

// --- Processes ----------------------------------------------------------------

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
  const info = await withQibocal(() => desktop.startServer(options))
  mergeProcess(info)
  if (!url && !info.url && options.ssh) {
    pending.set(info.id, options)
    return info
  }
  const address = url || info.url || `http://${options.host || '127.0.0.1'}:${options.port}`
  await rememberLaunch(address, options)
  return info
}

/** Open a notebook session, installing the command line first if needed. */
export async function startNotebook(options) {
  const info = await withQibocal(() => desktop.startNotebook(options))
  mergeProcess(info)
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

function mergeProcess(info) {
  const index = state.processes.findIndex(process => process.id === info.id)
  if (index >= 0) state.processes[index] = info
  else state.processes.push(info)

  // An installation that ended changed what the launcher can find.
  if (info.kind === 'setup' && info.status !== 'running') settleSetup(info)

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
}

// --- The dashboard and the registered servers ------------------------------------

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
