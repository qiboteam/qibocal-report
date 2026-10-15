import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import ServersView from './views/ServersView.vue'
import ProcessesView from './views/ProcessesView.vue'
import NotebooksView from './views/NotebooksView.vue'
import SettingsView from './views/SettingsView.vue'
import NotificationsView from './views/NotificationsView.vue'

/**
 * The launcher sections, described once: the router, the home page cards and
 * the system menu are all generated from this list.
 */
export const sections = [
  {
    name: 'home',
    path: '/',
    component: HomeView,
    title: 'Home',
    icon: 'Home',
    accelerator: 'CmdOrCtrl+1',
    summary: 'Everything the launcher can do, one click away.'
  },
  {
    name: 'servers',
    path: '/servers',
    component: ServersView,
    title: 'Servers',
    icon: 'Server',
    accelerator: 'CmdOrCtrl+2',
    summary: 'Start a report server here or on another machine, or register one you reach.'
  },
  {
    name: 'processes',
    path: '/processes',
    component: ProcessesView,
    title: 'Running',
    icon: 'Activity',
    accelerator: 'CmdOrCtrl+3',
    summary: 'Follow the output of everything the launcher started, stop it or start it again.'
  },
  {
    name: 'notebooks',
    path: '/notebooks',
    component: NotebooksView,
    title: 'Notebooks',
    icon: 'BookOpen',
    accelerator: 'CmdOrCtrl+4',
    summary: 'Open a JupyterLab or Marimo session here, over SSH or through a SLURM partition.'
  },
  {
    name: 'settings',
    path: '/settings',
    component: SettingsView,
    title: 'Configuration',
    icon: 'Settings',
    accelerator: 'CmdOrCtrl+5',
    summary: 'Which qibocal-report the launcher drives, and the configuration it shares with it.'
  }
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    ...sections.map(({ name, path, component }) => ({ name, path, component })),
    // Reached from the status bar, not a section: no card, no menu item.
    { name: 'notifications', path: '/notifications', component: NotificationsView },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ],
  scrollBehavior() {
    return { top: 0 }
  }
})
