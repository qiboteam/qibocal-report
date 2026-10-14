/**
 * The web frontend, embedded verbatim.
 *
 * Nothing is forked: this page mounts the very same application that is
 * deployed on the web, and only adds a bar to step back into the launcher.
 */
import { createApp } from 'vue'
import App from '@dashboard/App.vue'
import { router } from '@dashboard/router.js'
import LauncherBar from './components/LauncherBar.vue'

import 'virtual:uno.css'
import '@dashboard/assets/style.css'
import './assets/launcher.css'

createApp(App).use(router).mount('#app')
createApp(LauncherBar).mount('#launcher-bar')
