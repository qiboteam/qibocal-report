<template>
  <div id="app" class="bg-[#f7f7f7] text-[#000000]" :style="{ '--diagnostics-height': `${footerHeight}px` }">
    <div class="app-page">
      <loading-spinner v-if="isNavigating" label="Loading..." />
      <router-view v-show="!isNavigating" />
    </div>
    <admin-footer @height="footerHeight = $event" />
    <login-modal />
    <register-modal />
  </div>
</template>

<script setup>
import { onMounted, watch, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { state, fetchServers } from './store.js'
import { announce } from './utils/desktop.js'
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
})
</script>
