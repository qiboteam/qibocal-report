import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router.js'

import 'virtual:uno.css'
// The very stylesheet the web frontend uses, so the two halves of the
// application share one look.
import '@dashboard/assets/style.css'
import './assets/launcher.css'

createApp(App).use(router).mount('#app')
