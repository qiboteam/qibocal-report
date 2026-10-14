/**
 * The web frontend, embedded verbatim.
 *
 * Nothing is forked: this page mounts the very same application that is
 * deployed on the web, and only adds the mark that leads back to the
 * launcher, plus the system menu — which belongs to the window, but whose
 * actions die with the page that installed them.
 */
import { createApp } from 'vue'
import App from '@dashboard/App.vue'
import { router } from '@dashboard/router.js'
import LauncherOverlay from './components/LauncherOverlay.vue'
import { desktop } from './bridge.js'
import { TEMPORARY_PREFIX } from './lib/servers.js'
import { installMenu } from './menu.js'
import { sections } from './router.js'

import './styles.js'

/**
 * What the dashboard may ask of the desktop, set before it mounts.
 *
 * The dashboard's server list is `servers.json` here, not the browser's
 * storage: whatever it saves is written to the file the command line and
 * the launcher read — except the servers the launcher started for a look,
 * which are published to the dashboard while they run and never registered.
 */
window.qibocalDesktop = {
  saveServers: servers =>
    desktop.saveServers(
      (Array.isArray(servers) ? servers : []).filter(
        server => !(typeof server?.id === 'string' && server.id.startsWith(TEMPORARY_PREFIX))
      )
    )
}

createApp(App).use(router).mount('#app')

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
