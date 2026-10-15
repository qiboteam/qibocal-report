/**
 * The web frontend, embedded verbatim.
 *
 * Nothing is forked: this page mounts the very same application that is
 * deployed on the web, and only adds the mark that leads back to the
 * launcher, plus the system menu — which belongs to the window, but whose
 * actions die with the page that installed them.
 */
import { createApp, markRaw } from 'vue'
import App from '@dashboard/App.vue'
import { router } from '@dashboard/router.js'
import LauncherOverlay from './components/LauncherOverlay.vue'
import NotificationBell from './components/NotificationBell.vue'
import { desktop } from './bridge.js'
import { launchKeys, serverUrl } from './lib/servers.js'
import { installMenu } from './menu.js'
import { sections } from './router.js'
import { installShortcuts } from './shortcuts.js'
import { state, fail, initialize, notify } from './state.js'
import { pageShortcuts } from './pagekeys.js'

import './styles.js'

/**
 * What the dashboard may ask of the desktop, set before it mounts.
 *
 * The dashboard's server list is `servers.json` here, not the browser's
 * storage: whatever it saves is written to the file the command line and
 * the launcher read. And the dashboard can ask which registered servers
 * the launcher manages — those it has ever started — and which of them
 * run right now, to show the managed ones only while they are up.
 */
window.qibocalDesktop = {
  saveServers: servers => desktop.saveServers(Array.isArray(servers) ? servers : []),
  managedServers: async () => {
    const [processes, preferences] = await Promise.all([
      desktop.processes().catch(() => []),
      desktop.preferences().catch(() => ({}))
    ])
    const running = processes
      .filter(process => process.kind === 'server' && process.status === 'running')
      .flatMap(process => launchKeys(process.url))
    const launched = Object.keys(preferences?.launches || {}).flatMap(launchKeys)
    return { running, managed: [...new Set([...running, ...launched])] }
  },
  normalize: serverUrl,
  /**
   * What the dashboard has to say goes where everything else is said: the
   * status bar on its server list, the bell on its other pages, and the
   * Notifications page — never a toast of its own.
   */
  notify: (message, kind = 'info') => (kind === 'error' ? fail(message) : notify(message)),
  /** Launcher components the dashboard renders in its own toolbars. */
  widgets: { bell: markRaw(NotificationBell) },
  /** The dashboard page on screen names itself, and its keys reach the cheatsheet. */
  pageShortcuts: page => { state.pageShortcuts = page ? pageShortcuts(page) : null },
  /** The address of a launcher section, for a link out of the dashboard. */
  launcherUrl: name => {
    const section = sections.find(entry => entry.name === name)
    const target = new URL('index.html', window.location.href)
    target.hash = `#${section?.path || '/'}`
    return target.href
  }
}

createApp(App).use(router).mount('#app')

// The launcher's state — processes, notifications, the command line — is
// read here too: the status bar, the bell and the closing dialog live on it.
initialize()

const overlay = createApp(LauncherOverlay)
overlay.provide('dashboardRoute', router.currentRoute)
overlay.mount('#launcher-overlay')

/** Open a launcher section, which from here means loading the other page. */
function goTo(name, query = '') {
  const section = sections.find(entry => entry.name === name)
  const target = new URL('index.html', window.location.href)
  target.hash = `#${section?.path || '/'}${query}`
  window.location.href = target.href
}

async function servers() {
  try {
    return await desktop.listServers()
  } catch {
    return []
  }
}

// The same keys as on the launcher page; a section is the other page here.
installShortcuts({
  go: name => goTo(name),
  dashboard: () => window.scrollTo({ top: 0, behavior: 'smooth' }),
  newServer: () => goTo('servers', '?new=1')
})

servers().then(registered =>
  installMenu({
    goTo,
    // The dashboard is already on screen; the item scrolls back to its top.
    openDashboard: () => window.scrollTo({ top: 0, behavior: 'smooth' }),
    // Starting one needs the launcher page, which opens on its form.
    launchServer: server => goTo('servers', `?server=${encodeURIComponent(server.id)}`),
    servers: registered
  })
)
