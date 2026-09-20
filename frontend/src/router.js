import { createRouter, createWebHashHistory } from 'vue-router'
import ServersView from './views/ServersView.vue'
import DashboardView from './views/DashboardView.vue'
import ReportView from './views/ReportView.vue'
import DocsView from './views/DocsView.vue'
import StatisticsView from './views/StatisticsView.vue'
import PlatformView from './views/PlatformView.vue'
import ArchivesView from './views/ArchivesView.vue'
import ServerAdminView from './views/ServerAdminView.vue'
import InviteRegisterView from './views/InviteRegisterView.vue'
import { state, fetchServers, checkActiveServerAuth, setActiveServer } from './store.js'

const routes = [
  {
    path: '/',
    name: 'root',
    redirect: async () => {
      await fetchServers()
      if (
        !state.activeServer ||
        state.servers.length === 0 ||
        !state.servers.some(s => s.id === state.activeServer?.id)
      ) {
        return { name: 'servers' }
      }
      if (state.auth?.enabled && (!state.auth?.token || !state.auth?.user)) {
        return { name: 'servers' }
      }
      return { name: 'dashboard' }
    }
  },
  { path: '/servers', name: 'servers', component: ServersView },
  { path: '/server-admin/:serverId?', name: 'server-admin', component: ServerAdminView },
  { path: '/invite/:token?', name: 'invite', component: InviteRegisterView },
  { path: '/dashboard', name: 'dashboard', component: DashboardView },
  { path: '/archives', name: 'archives', component: ArchivesView },
  { path: '/statistics', name: 'statistics', component: StatisticsView },
  { path: '/platform/:id(.*)', name: 'platform', component: PlatformView },
  {
    path: '/reports/:id(.*)/platform',
    redirect: to => ({ name: 'platform', params: { id: to.params.id }, query: to.query })
  },
  { path: '/reports/:id(.*)', name: 'report', component: ReportView },
  { path: '/docs/:page(.*)?', name: 'docs', component: DocsView }
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// Navigation Guard: Protect internal pages from unauthenticated access
router.beforeEach(async (to, from, next) => {
  // 1. Documentation, Server Management, and Invite routes are universally public
  if (
    to.name === 'docs' ||
    to.path.startsWith('/docs') ||
    to.name === 'servers' ||
    to.path === '/servers' ||
    to.name === 'invite' ||
    to.path.startsWith('/invite')
  ) {
    return next()
  }

  // 2. Ensure servers are loaded
  await fetchServers()

  // If no server is registered or active, user cannot view any internal server pages
  if (
    !state.activeServer ||
    state.servers.length === 0 ||
    !state.servers.some(s => s.id === state.activeServer?.id)
  ) {
    setActiveServer(null)
    return next({ name: 'servers' })
  }

  // 3. Ensure auth status has been verified for active server
  if (!state.auth?.checked) {
    await checkActiveServerAuth(state.activeServer)
  }

  // 4. If authentication is enabled and user is not authenticated, block internal pages
  if (state.auth?.enabled && (!state.auth?.token || !state.auth?.user)) {
    state.auth.errorMessage = 'Authentication required. Please sign in to access that page.'
    return next('/servers')
  }

  // 5. If navigating to Server Administration, require Admin role
  if (to.name === 'server-admin' && state.auth?.enabled && state.auth?.user?.role !== 'admin') {
    state.auth.errorMessage = 'Administrator role required to access Server Administration.'
    return next('/dashboard')
  }

  return next()
})

