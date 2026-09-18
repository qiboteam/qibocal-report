import { createRouter, createWebHashHistory } from 'vue-router'
import ServersView from './views/ServersView.vue'
import DashboardView from './views/DashboardView.vue'
import ReportView from './views/ReportView.vue'
import DocsView from './views/DocsView.vue'
import StatisticsView from './views/StatisticsView.vue'
import PlatformView from './views/PlatformView.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/servers', name: 'servers', component: ServersView },
  { path: '/dashboard', name: 'dashboard', component: DashboardView },
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
