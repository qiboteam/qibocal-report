<template>
  <div id="app" class="min-h-screen bg-[#f7f7f7] text-[#000000]">
    <router-view />
    <login-modal />
    <register-modal />
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { state, fetchServers } from './store.js'
import LoginModal from './components/modals/LoginModal.vue'
import RegisterModal from './components/modals/RegisterModal.vue'

const router = useRouter()
const route = useRoute()

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
