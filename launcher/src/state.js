import { reactive, computed, watch } from 'vue'
import { desktop, isDesktop, openInNewWindow, subscribe } from './bridge.js'
import { defaultLaunch, launchKeys, syncDashboardServers, serverUrl } from './lib/servers.js'
import { installationBehind } from './lib/versions.js'
import { processNews, unattended } from './lib/alerts.js'
import { loadNotices, nextNoticeId, storeNotices } from './lib/notices.js'
import { queueKey, queueOf } from './lib/slurm.js'

export const LOG_EVENT = 'launcher://log'
export const PROCESS_EVENT = 'launcher://process'
/** The launcher is closing and waits for processes: show them, offer to force it. */
export const CLOSING_EVENT = 'launcher://closing'

/** Where the notifications outlive a page change within the window. */
const session = typeof sessionStorage === 'undefined' ? null : sessionStorage

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
  /** Everything said so far, newest first; archived ones are put away, not lost. */
  notifications: loadNotices(session),
  /** How each process was started, by process id, so a run can be repeated. */
  launches: {},
  /** The processes the closing launcher waits for; null while it is not closing. */
  closing: null,
  /** Whether the keyboard shortcuts are on screen, as GitHub shows them on `?`. */
  cheatsheet: false,
  /** The keys of the page on screen — `{ title, entries }` — or null. */
  pageShortcuts: null,
  /** What each SLURM queue answered, by `queueKey`: `{ data, error, loading, fetchedAt }`. */
  queues: {}
})

// What is said on one page is still there on the other.
watch(() => state.notifications, notices => storeNotices(session, notices), { deep: true })

/** What is new: said and not yet archived. */
export const inbox = computed(() => state.notifications.filter(entry => !entry.archived))

export const hasQibocal = computed(() => Boolean(state.environment?.executable))

/** Whether the launcher is installing or updating its own qibocal-report right now. */
export const installing = computed(() =>
  state.processes.some(process => process.kind === 'setup' && process.status === 'running')
)

// --- Messages ---------------------------------------------------------------

/** How many notifications are kept, newest first. */
const NOTIFICATION_LIMIT = 50

let messageTimer = null
let counter = nextNoticeId(state.notifications) - 1

/**
 * Say something in the status bar, and let it fade on its own.
 *
 * Messages never interrupt: the latest shows in the bottom-right corner
 * until it fades, and all of them stay in the list behind the counter
 * next to it, each until dismissed. Nothing moves on the page.
 */
function say(text, kind, link = null) {
  counter += 1
  const entry = { id: counter, text, kind, at: Date.now(), link: toRoute(link), archived: false }
  state.notifications.unshift(entry)
  if (state.notifications.length > NOTIFICATION_LIMIT) state.notifications.length = NOTIFICATION_LIMIT
  clearTimeout(messageTimer)
  state.message = entry
  messageTimer = setTimeout(() => {
    if (state.message?.id === entry.id) state.message = null
  }, MESSAGE_TTL[kind])
}

/**
 * The section a message is about, as a route: a name such as `processes`,
 * or a full route location; nothing when the message belongs nowhere.
 */
function toRoute(link) {
  if (!link) return null
  return typeof link === 'string' ? { name: link } : link
}

/** Say something, optionally pointing at the section it is about. */
export function notify(message, link = null) {
  say(message, 'info', link)
}

export function fail(error, link = null) {
  say(typeof error === 'string' ? error : (error?.message || String(error)), 'error', link)
}

export function dismissNotification(id) {
  state.notifications = state.notifications.filter(entry => entry.id !== id)
  if (state.message?.id === id) state.message = null
}

/** Put an entry away, as GitHub marks a notification done: out of the inbox, kept. */
export function archiveNotification(id) {
  const entry = state.notifications.find(item => item.id === id)
  if (entry) entry.archived = true
  if (state.message?.id === id) state.message = null
}

export function unarchiveNotification(id) {
  const entry = state.notifications.find(item => item.id === id)
  if (entry) entry.archived = false
}

export function archiveAll() {
  state.notifications.forEach(entry => { entry.archived = true })
  state.message = null
}

export function clearArchived() {
  state.notifications = state.notifications.filter(entry => !entry.archived)
}

export function dismiss() {
  clearTimeout(messageTimer)
  state.message = null
  state.notifications = []
}

/**
 * Run an action, surfacing its failure in the status bar instead of the
 * console; `link` is the section both the success and the failure concern.
 */
export async function attempt(action, success = null, link = null) {
  try {
    const result = await action()
    if (success) notify(typeof success === 'function' ? success(result) : success, link)
    return result
  } catch (error) {
    fail(error, link)
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
/** Whether the installation was already brought up to this build once: one try a session. */
let followedBuild = false

/**
 * Make sure the command line is there, installing it if it is not, and
 * up to date with this launcher, updating it if it is not.
 *
 * Nothing is installed on opening the application: the first server,
 * notebook or invitation that needs qibocal-report starts the installation,
 * and goes on by itself once it is done — with a word in the status bar
 * meanwhile, and the output in Running. The launcher's own installation
 * follows the build, or the version chosen in Configuration: a launcher
 * newer than what it installed updates it first, so that the command line
 * takes what the launcher asks of it. Should that update fail — offline,
 * say — the installed one serves, and it is not tried again this session.
 */
export async function ensureQibocal() {
  const behind = hasQibocal.value && !followedBuild && installationBehind(state.environment)
  if (hasQibocal.value && !behind) return
  if (!hasQibocal.value && !state.environment?.python) {
    fail('No Python 3.10 or newer was found to install qibocal-report with.', 'settings')
    throw new Error('No Python 3.10 or newer was found to install qibocal-report with; see Configuration.')
  }
  if (behind) followedBuild = true
  if (!installing.value) await installQibocal(behind)
  try {
    await new Promise((resolve, reject) => awaitingSetup.push({ resolve, reject }))
  } catch (error) {
    if (!behind) throw error
    notify('qibocal-report could not be updated to this build; carrying on with the installed one.', 'settings')
  }
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
    notify(waiting.length ? 'qibocal-report is installed; carrying on.' : 'qibocal-report is installed.', 'settings')
    waiting.forEach(entry => entry.resolve())
    return
  }
  const reason = info.status === 'failed'
    ? 'The installation of qibocal-report failed; its output is in Running.'
    : 'qibocal-report is still missing after the installation; see Running.'
  waiting.forEach(entry => entry.reject(new Error(reason)))
  if (!waiting.length) fail(reason, 'processes')
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

/**
 * Replace what is remembered about a server: its old address and its new
 * one forget their launches, and the new address takes `options` — or
 * nothing, for a server the launcher is not to start any more.
 */
export async function rewriteLaunch(previousUrl, url, options) {
  const launches = { ...(state.preferences.launches || {}) }
  for (const key of [...launchKeys(previousUrl), ...launchKeys(url)]) delete launches[key]
  if (options && serverUrl(url)) launches[serverUrl(url)] = options
  state.preferences = await desktop.savePreferences({ ...state.preferences, launches })
}

export function recallLaunch(url) {
  const launches = state.preferences.launches || {}
  for (const key of launchKeys(url)) {
    if (launches[key]) return launches[key]
  }
  return null
}

/**
 * How a registered server is started: as it was last time, or — for one the
 * launcher never started — on this machine at its registered address,
 * serving the shared directory. Nothing for an address that is not here.
 */
export function launchOptionsFor(server) {
  return recallLaunch(server?.url) || defaultLaunch(server)
}

/** The running process behind a registered server, if any. */
export function processFor(server) {
  const keys = new Set(launchKeys(server?.url))
  return runningServers().find(process => launchKeys(process.url).some(key => keys.has(key))) || null
}

/**
 * Launches still waiting for an address, by process.
 *
 * A server started over SSH is reached through a tunnel whose local port is
 * only known once the command line prints it, so its options are kept here
 * until `mergeProcess` sees that address go by — together with the
 * registered server being brought up again, if any, whose entry then takes
 * the new address instead of a second entry appearing next to it.
 */
const pending = new Map()

/**
 * Start a report server and keep its options for the next time.
 *
 * `url` is the address of the registered server being started again, when
 * there is one: its entry is what the new address belongs to.
 */
export async function startServer(options, { url = null } = {}) {
  const info = await withQibocal(() => desktop.startServer(options))
  state.launches[info.id] = { kind: 'server', options, url }
  mergeProcess(info)
  if (!info.url && options.ssh) {
    pending.set(info.id, { options, url })
    return info
  }
  const address = url || info.url || `http://${options.host || 'localhost'}:${options.port}`
  await rememberLaunch(address, options)
  return info
}

/** Wait for a process to end, a few seconds at most; true when it did. */
export async function awaitExit(id, timeoutMs = 15_000) {
  const until = Date.now() + timeoutMs
  while (Date.now() < until) {
    const process = processById(id)
    if (!process || (process.status !== 'running' && process.status !== 'stopping')) return true
    await new Promise(resolve => setTimeout(resolve, 200))
  }
  return false
}

/**
 * Bring a registered server's qibocal-report up to date, and start it
 * again. A server on another machine has `qibocal report server upgrade`
 * run against its environment — a process of its own, in Running — and is
 * started once that is done; one on this machine runs the launcher's own
 * installation, which is updated first. A running server is stopped, and
 * comes back at the same entry.
 */
export async function updateServerInstallation(server) {
  const options = launchOptionsFor(server)
  if (!options) throw new Error('Registered elsewhere: nothing to update from this machine.')
  const running = processFor(server)
  if (running) {
    await desktop.stopProcess(running.id)
    if (!(await awaitExit(running.id))) throw new Error('The server did not stop in time.')
  }
  if (!options.ssh) {
    // The launcher's own installation: updated, awaited, then the server as before.
    const setup = await installQibocal(true)
    await awaitExit(setup.id, 30 * 60_000)
    await refreshEnvironment()
    return startServer(options, { url: server.url })
  }
  const update = await withQibocal(() => desktop.upgradeServer({
    name: options.name || server.name || null,
    ssh: options.ssh,
    workdir: options.workdir || null,
    venv: options.venv || null,
    install: options.install || null,
    timeout: options.timeout || null
  }))
  mergeProcess(update)
  if (!(await awaitExit(update.id, 30 * 60_000))) throw new Error('The update did not finish in time; see Running.')
  const done = processById(update.id)
  if (!done || done.status !== 'exited') throw new Error(`The update failed; its output is in Running.`)
  return startServer(options, { url: server.url })
}

/** Open a notebook session, installing the command line first if needed. */
export async function startNotebook(options) {
  const info = await withQibocal(() => desktop.startNotebook(options))
  state.launches[info.id] = { kind: 'notebook', options, url: null }
  mergeProcess(info)
  // Dispatched to a partition: its queue is asked now, so the answer is
  // there by the time Running shows the card — one question, shared with
  // the panel that follows, which asks again only when this one has aged.
  const queue = queueOf(options)
  if (queue) refreshQueue(queue).catch(() => {})
  return info
}

/** Run a process again, as it was started: the same options, the same entry. */
export async function restartProcess(process) {
  const launch = state.launches[process.id]
  if (!launch) throw new Error('The launcher does not know how this was started.')
  if (launch.kind === 'notebook') return startNotebook(launch.options)
  return startServer(launch.options, { url: launch.url || process.url })
}

/**
 * A registered server came up at a new address: move its entry there, and
 * drop the entry the command line registered for the new address meanwhile.
 */
async function readdress(previousUrl, newUrl) {
  const previous = new Set(launchKeys(previousUrl))
  const fresh = new Set(launchKeys(newUrl))
  const entry = state.servers.find(server => launchKeys(server.url).some(key => previous.has(key)))
  if (!entry || fresh.has(serverUrl(entry.url))) return
  const servers = state.servers
    .filter(server => server === entry || !launchKeys(server.url).some(key => fresh.has(key)))
    .map(server => (server === entry ? { ...server, url: serverUrl(newUrl) } : server))
  state.servers = await desktop.saveServers(servers)
  const launches = { ...(state.preferences.launches || {}) }
  for (const key of previous) {
    if (launches[key]) {
      launches[serverUrl(newUrl)] = launches[key]
      delete launches[key]
    }
  }
  state.preferences = await desktop.savePreferences({ ...state.preferences, launches })
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

/**
 * Say it where everything is said and — when the user is not looking at
 * `page`, or at the window at all — through the system as well.
 */
export function alert(title, body, { page = null, link = null } = {}) {
  notify(body, link)
  if (!isDesktop || typeof document === 'undefined') return
  const away = unattended({
    hidden: document.visibilityState === 'hidden',
    focused: document.hasFocus(),
    hash: window.location.hash,
    page
  })
  if (away) desktop.systemNotify(title, body).catch(() => {})
}

function mergeProcess(info) {
  const index = state.processes.findIndex(process => process.id === info.id)
  const previous = index >= 0 ? state.processes[index] : null
  if (index >= 0) state.processes[index] = info
  else state.processes.push(info)

  // A server up, a session ready, a failure: news, when nobody is watching Running.
  const news = processNews(previous, info)
  if (news) alert(news.title, news.body, { page: '/processes', link: 'processes' })

  // An installation that ended changed what the launcher can find.
  if (info.kind === 'setup' && info.status !== 'running') settleSetup(info)

  const waiting = pending.get(info.id)
  if (!waiting) return
  if (info.url) {
    pending.delete(info.id)
    if (waiting.url && !launchKeys(waiting.url).includes(serverUrl(info.url))) {
      readdress(waiting.url, info.url).then(() => refreshServers()).catch(error => fail(error, 'servers'))
    } else {
      // The command line registers the new address; a moment later it is in the list.
      setTimeout(refreshServers, 1500)
    }
    rememberLaunch(info.url, waiting.options)
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
  await subscribe(CLOSING_EVENT, payload => {
    state.closing = { ids: Array.isArray(payload?.ids) ? payload.ids : [] }
  })

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
 * dashboard reads the instances the launcher just registered. Opening a
 * running server that is not registered yet registers it first: the
 * dashboard only knows registered servers.
 */
export async function openDashboard(preferredUrl = null, { newWindow = false } = {}) {
  if (preferredUrl) {
    const keys = new Set(launchKeys(preferredUrl))
    const registered = state.servers.some(server => launchKeys(server.url).some(key => keys.has(key)))
    if (!registered) {
      const process = runningServers().find(entry => launchKeys(entry.url).some(key => keys.has(key)))
      try {
        await registerServer({
          name: process?.label || undefined,
          url: preferredUrl,
          description: process ? `Started by the launcher: ${process.detail}` : `Server at ${preferredUrl}`
        })
      } catch (error) {
        fail(error, 'servers')
        return
      }
    }
  }
  syncDashboardServers(state.servers, { preferredUrl })
  const target = new URL('dashboard.html', window.location.href)
  if (preferredUrl) target.hash = '#/dashboard'
  // In a new window when asked — a modifier held, the middle button, Shift+Enter.
  if (newWindow) openInNewWindow(target.href)
  else window.location.href = target.href
}

/**
 * Close the launcher: `force` kills whatever is still running first.
 * Without it, the native side waits for the processes it is stopping.
 */
/** Quit as the menu does: the processes stopped and waited for, the dialog shown meanwhile. */
export async function requestQuit() {
  await desktop.requestQuit()
}

export async function quit(force = false) {
  await desktop.quit(force)
}

// --- SLURM queues -------------------------------------------------------------

/** How often a queue on screen is asked, in seconds: a preference, never under ten. */
export const queuePollSeconds = computed(() => {
  const value = Number(state.preferences?.queuePollSeconds)
  return Number.isFinite(value) && value > 0 ? Math.max(10, Math.round(value)) : 30
})

/** The entry of a queue, or null before it was ever asked. */
export function queueEntry(queue) {
  return state.queues[queueKey(queue)] || null
}

const queueWatchers = new Map()

/**
 * Ask a queue — unless it was asked a moment ago, in which case the last
 * answer stands; `force` asks anyway. One question at a time per queue:
 * every panel on the same queue shares it.
 */
export async function refreshQueue(queue, { force = false } = {}) {
  const key = queueKey(queue)
  if (!key) return null
  const entry = state.queues[key] || (state.queues[key] = { data: null, error: null, loading: false, fetchedAt: 0 })
  const minimum = (queuePollSeconds.value * 1000) / 2
  if (entry.loading) return entry
  if (!force && entry.fetchedAt && Date.now() - entry.fetchedAt < minimum) return entry
  entry.loading = true
  try {
    const data = await withQibocal(() => desktop.slurmQueue({ ssh: queue.ssh, partition: queue.partition, timeout: 30 }))
    entry.data = data
    entry.error = data?.error || null
    entry.fetchedAt = Date.now()
  } catch (error) {
    entry.error = error?.message || String(error)
    entry.fetchedAt = entry.fetchedAt || Date.now()
  } finally {
    entry.loading = false
  }
  return entry
}

/**
 * Keep a queue fresh while something looks at it: asked now, then every
 * `queuePollSeconds`; the timer stops with the last watcher. Answers the
 * function that stops watching.
 */
export function watchQueue(queue) {
  const key = queueKey(queue)
  if (!key) return () => {}
  let watcher = queueWatchers.get(key)
  if (!watcher) {
    watcher = { count: 0, timer: null }
    queueWatchers.set(key, watcher)
    const tick = () => {
      refreshQueue(queue).finally(() => {
        if (queueWatchers.get(key) === watcher && watcher.count > 0) {
          watcher.timer = setTimeout(tick, queuePollSeconds.value * 1000)
        }
      })
    }
    tick()
  }
  watcher.count += 1
  return () => {
    watcher.count -= 1
    if (watcher.count <= 0) {
      clearTimeout(watcher.timer)
      queueWatchers.delete(key)
    }
  }
}

/**
 * Register a server address in `servers.json`, without duplicating it.
 *
 * The address identifies a reachable server; the name identifies one the
 * launcher starts, which comes up at a new tunnel port each time: an entry
 * of the same name moves to the new address rather than gaining a twin.
 */
export async function registerServer(server) {
  const url = serverUrl(server.url)
  if (!url) throw new Error('Enter the address of the report server.')
  const servers = [...state.servers]
  const name = typeof server.name === 'string' ? server.name.trim() : ''
  let index = servers.findIndex(entry => serverUrl(entry.url) === url)
  if (index < 0 && name) index = servers.findIndex(entry => entry.name === name)
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

/** Change what a registered server is called, where it is, how it is described. */
export async function updateServer(id, changes) {
  const index = state.servers.findIndex(server => server.id === id)
  if (index < 0) throw new Error('This server is no longer registered.')
  const url = serverUrl(changes.url ?? state.servers[index].url)
  if (!url) throw new Error('Enter the address of the report server.')
  const taken = state.servers.some((server, position) => position !== index && serverUrl(server.url) === url)
  if (taken) throw new Error('Another server is registered at this address.')
  const servers = [...state.servers]
  servers[index] = { ...servers[index], ...changes, url }
  state.servers = await desktop.saveServers(servers)
  return servers[index]
}

export async function forgetServer(id) {
  state.servers = await desktop.saveServers(state.servers.filter(server => server.id !== id))
}
