import { createRouter, createWebHistory } from 'vue-router'
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
    component: { template: '<div></div>' },
    beforeEnter: async (to, from, next) => {
      await fetchServers()
      if (
        !state.activeServer ||
        state.servers.length === 0 ||
        !state.servers.some(s => s.id === state.activeServer?.id)
      ) {
        return next({ name: 'servers' })
      }
      if (state.auth?.enabled && (!state.auth?.token || !state.auth?.user)) {
        return next({ name: 'servers' })
      }
      return next({ name: 'dashboard' })
    }
  },
  { path: '/servers', name: 'servers', component: ServersView },
  { path: '/admin/:serverId?', name: 'admin', component: ServerAdminView },
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
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// Navigation Guard: Protect internal pages from unauthenticated access
router.beforeEach(async (to, from, next) => {
  // 1. Admin route is always allowed - never redirect away from it.
  //    Component itself checks admin permission and shows access-denied UI.
  if (to.name === 'admin' || to.path.startsWith('/admin')) {
    await fetchServers()
    return next()
  }

  // 2. Documentation, Server Management, and Invite routes are public
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

  // 3. Ensure servers are loaded
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

  // 4. Ensure auth status has been verified for active server
  if (!state.auth?.checked) {
    await checkActiveServerAuth(state.activeServer)
  }

  // 5. If authentication is enabled and user is not authenticated, block internal pages
  if (state.auth?.enabled && (!state.auth?.token || !state.auth?.user)) {
    state.auth.errorMessage = 'Authentication required. Please sign in to access that page.'
    return next('/servers')
  }

  return next()
})

