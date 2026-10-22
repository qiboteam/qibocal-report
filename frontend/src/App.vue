<template>
  <div id="app" class="bg-[#f7f7f7] text-[#000000]" :style="{ '--diagnostics-height': `${footerHeight}px` }">
    <div class="app-page">
      <loading-spinner v-if="isNavigating" label="Loading..." />
      <router-view v-show="!isNavigating" />
    </div>
    <admin-footer @height="footerHeight = $event" />
    <login-modal />
    <register-modal />
    <shortcuts-modal />
    <file-viewer-modal />
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, watch, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { state, fetchServers, getAuthHeader } from './store.js'
import { alert, announce, inDesktop } from './utils/desktop.js'
import { createArrivals, describeArrivals } from './utils/arrivals.js'
import { getActiveServerUrl } from './utils/url.js'
import { cheatsheetOpen, isPlainKey, isTypingTarget } from './utils/shortcuts.js'
import ShortcutsModal from './components/modals/ShortcutsModal.vue'
import FileViewerModal from './components/modals/FileViewerModal.vue'
import LoginModal from './components/modals/LoginModal.vue'
import RegisterModal from './components/modals/RegisterModal.vue'
import LoadingSpinner from './components/LoadingSpinner.vue'
import AdminFooter from './components/diagnostics/AdminFooter.vue'

const router = useRouter()
const route = useRoute()
const isNavigating = ref(false)
const footerHeight = ref(0)

router.beforeEach((to, from, next) => {
  // Show spinner when navigating between different routes
  if (to.path !== from.path) {
    isNavigating.value = true
  }
  next()
})

router.afterEach(() => {
  // Hide spinner after navigation completes
  isNavigating.value = false
})

/**
 * The keys that work everywhere in the dashboard, as on GitHub: `g s` to
 * the report servers, `g l` to the report list, `?` for the list of keys.
 * Inside the launcher, `?` is the launcher's: its cheatsheet lists these.
 */
let chord = null
let chordTimer = null
function forgetChord() {
  chord = null
  clearTimeout(chordTimer)
}
function onGlobalKeydown(event) {
  if (!isPlainKey(event) || isTypingTarget(event)) return
  if (event.key === 'Escape') {
    forgetChord()
    if (cheatsheetOpen.value) {
      cheatsheetOpen.value = false
      event.preventDefault()
    }
    return
  }
  if (event.key === '?') {
    forgetChord()
    if (inDesktop()) return
    cheatsheetOpen.value = !cheatsheetOpen.value
    event.preventDefault()
    return
  }
  if (event.shiftKey) return
  if (chord === 'g') {
    forgetChord()
    if (event.key === 's') router.push('/servers')
    else if (event.key === 'l') router.push('/dashboard')
    else return
    cheatsheetOpen.value = false
    event.preventDefault()
    return
  }
  if (event.key === 'g') {
    chord = 'g'
    clearTimeout(chordTimer)
    chordTimer = setTimeout(forgetChord, 1500)
  }
}
onMounted(() => document.addEventListener('keydown', onGlobalKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onGlobalKeydown))

// Inside the launcher, an authentication failure is a notification like any
// other — in the status bar, on the bell, red — not a banner of this page.
watch(() => state.auth?.errorMessage, message => {
  if (message && announce(message, 'error')) state.auth.errorMessage = ''
})

watch(
  () => [state.activeServer, state.servers.length, state.auth.enabled, state.auth.token, state.auth.user, route.path],
  () => {
    const isPublic =
      route.name === 'docs' ||
      route.path.startsWith('/docs') ||
      route.name === 'servers' ||
      route.path === '/servers' ||
      route.name === 'invite' ||
      route.path.startsWith('/invite') ||
      route.name === 'admin' ||
      route.path.startsWith('/admin')
    if (!isPublic) {
      if (!state.activeServer || state.servers.length === 0 || !state.servers.some(s => s.id === state.activeServer?.id)) {
        router.push('/servers')
        return
      }
      if (state.auth?.enabled && (!state.auth?.token || !state.auth?.user)) {
        router.push('/servers')
      }
    }
  }
)

onMounted(() => {
  fetchServers()
  watchArrivals()
})

// Inside the launcher, new reports on a server are news even when the list
// is not on screen: each registered server is asked for its count now and
// then — the health answer, which the server keeps ready — and an increase
// goes through the launcher, to the bell and, when nobody is looking, the
// system. Nothing of this in a browser.
const ARRIVALS_EVERY_MS = 60_000
const arrivals = createArrivals()
let arrivalsTimer = null

async function countArrivals() {
  for (const server of state.servers || []) {
    const base = getActiveServerUrl(server)
    if (!base) continue
    try {
      // With the token: an authenticated server counts nothing for a stranger.
      const response = await fetch(`${base}/api/health`, { headers: getAuthHeader(server), cache: 'no-store', signal: AbortSignal.timeout(5000) })
      if (!response.ok) continue
      const health = await response.json()
      const fresh = arrivals(base, Number(health?.reports_count))
      if (fresh > 0) alert('New reports', describeArrivals(fresh, server.name || base))
    } catch {
      // A server away says nothing; it is asked again next time.
    }
  }
}

function watchArrivals() {
  if (!inDesktop() || arrivalsTimer) return
  countArrivals()
  arrivalsTimer = setInterval(countArrivals, ARRIVALS_EVERY_MS)
}

onBeforeUnmount(() => {
  clearInterval(arrivalsTimer)
  arrivalsTimer = null
})
</script>
