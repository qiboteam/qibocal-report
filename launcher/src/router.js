import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import ServersView from './views/ServersView.vue'
import ProcessesView from './views/ProcessesView.vue'
import NotebooksView from './views/NotebooksView.vue'
import SettingsView from './views/SettingsView.vue'
import NotificationsView from './views/NotificationsView.vue'
import HelpView from './views/HelpView.vue'
import QueuesView from './views/QueuesView.vue'
import RemotesView from './views/RemotesView.vue'
import AgentsView from './views/AgentsView.vue'
import AgentsSetupView from './views/AgentsSetupView.vue'

/**
 * The launcher sections, described once: the router, the home page cards,
 * the system menu, the keyboard shortcuts and the Help page are all
 * generated from this list.
 *
 * `accelerator` is the menu shortcut, a mnemonic letter with the modifier
 * — Configuration takes the one every application gives its preferences;
 * `key` is the letter that follows `g` on the keyboard, as on GitHub:
 * `g s` goes to Servers.
 */
export const sections = [
  {
    name: 'home',
    path: '/',
    component: HomeView,
    title: 'Home',
    icon: 'Home',
    accelerator: 'CmdOrCtrl+Shift+H',
    key: 'h',
    summary: 'Everything the launcher can do, one click away.'
  },
  {
    name: 'servers',
    path: '/servers',
    component: ServersView,
    title: 'Servers',
    icon: 'Server',
    accelerator: 'CmdOrCtrl+Shift+S',
    key: 's',
    summary: 'Start a report server here or on another machine, or register one you reach.'
  },
  {
    name: 'processes',
    path: '/processes',
    component: ProcessesView,
    title: 'Running',
    icon: 'Activity',
    accelerator: 'CmdOrCtrl+Shift+R',
    key: 'r',
    summary: 'Follow the output of everything the launcher started, stop it or start it again.'
  },
  {
    name: 'notebooks',
    path: '/notebooks',
    component: NotebooksView,
    title: 'Notebooks',
    icon: 'BookOpen',
    accelerator: 'CmdOrCtrl+Shift+B',
    key: 'b',
    summary: 'Open a JupyterLab or Marimo session here, over SSH or through a SLURM partition.'
  },
  {
    name: 'agents',
    path: '/agents',
    component: AgentsView,
    title: 'Agents',
    icon: 'Bot',
    accelerator: 'CmdOrCtrl+Shift+A',
    key: 'a',
    summary: 'The configurations of the Qibocal MCP servers and agents, here and on access nodes, and autonomous runs.'
  },
  {
    name: 'settings',
    path: '/settings',
    component: SettingsView,
    title: 'Configuration',
    icon: 'Settings',
    accelerator: 'CmdOrCtrl+Comma',
    key: 'c',
    summary: 'Which qibocal-report the launcher drives, and the configuration it shares with it.'
  },
  {
    name: 'help',
    path: '/help',
    component: HelpView,
    title: 'Help',
    icon: 'HelpCircle',
    accelerator: 'CmdOrCtrl+Slash',
    key: '?',
    summary: 'How the launcher works, section by section, and every keyboard shortcut.'
  }
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    ...sections.map(({ name, path, component }) => ({ name, path, component })),
    // Reached from the status bar, not a section: no card, no menu item.
    { name: 'notifications', path: '/notifications', component: NotificationsView },
    // One page of the Help, past its overview.
    { name: 'help-page', path: '/help/:page', component: HelpView },
    // A tab of Notebooks: the connections a session hands its acquisitions to.
    { name: 'remotes', path: '/notebooks/remote', component: RemotesView },
    // Reached from Agents: what its configurations share.
    { name: 'agents-setup', path: '/agents/setup', component: AgentsSetupView },
    // Reached from Running, where a session waits in its queue.
    { name: 'queues', path: '/queues', component: QueuesView },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ],
  scrollBehavior() {
    return { top: 0 }
  }
})
