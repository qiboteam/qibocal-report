<template>
  <div class="min-h-screen bg-[#f7f7f7] text-[#000000] flex flex-col">
    <header class="sticky top-0 z-20 bg-[#f7f7f7]/85 backdrop-blur border-b border-gray-200/60">
      <!--
        Nothing but the mark and the dashboard: the sections are one Go menu
        away, with their accelerators, and the home page lists them again
        with the figures a navigation bar cannot show.
      -->
      <div class="max-w-5xl mx-auto px-5 h-14 flex items-center gap-3">
        <router-link to="/" class="lx-logo" title="Qibocal home" aria-label="Qibocal home">
          <launcher-logo />
        </router-link>

        <!-- Qibocal being installed in the background: said here, on every page. -->
        <router-link
          v-if="installing"
          to="/processes"
          class="ml-auto inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#f7f5ff] text-[11px] font-medium text-[#3b107e] hover:bg-[#ebe0ff] transition"
          title="Follow the installation in Running"
        >
          <Loader2 class="w-3.5 h-3.5 lx-spin" />
          Installing Qibocal…
        </router-link>

        <button
          type="button"
          class="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#833dff] text-white hover:bg-[#722ce6] active:scale-[0.98] transition shadow-2xs"
          :class="{ 'ml-auto': !installing }"
          @click="openDashboard()"
        >
          Dashboard
        </button>
      </div>
    </header>

    <div v-if="state.notice || state.error" class="max-w-5xl mx-auto w-full px-5 pt-4">
      <div
        class="px-3.5 py-2.5 rounded-xl text-xs flex items-start gap-2 shadow-2xs animate-fade-in"
        :class="state.error ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-800'"
      >
        <span class="font-medium whitespace-pre-wrap flex-1">{{ state.error || state.notice }}</span>
        <button type="button" class="text-current opacity-60 hover:opacity-100" @click="dismiss">
          <X class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <main class="flex-1 w-full">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Loader2, X } from 'lucide-vue-next'
import LauncherLogo from './components/LauncherLogo.vue'
import { installMenu } from './menu.js'
import {
  state,
  dismiss,
  fail,
  initialize,
  installing,
  openDashboard,
  recallLaunch,
  startServer
} from './state.js'

const router = useRouter()

/**
 * Bring a registered server up again with the options it was started with,
 * or open its form when the launcher has never started it.
 */
async function launchServer(server) {
  const options = recallLaunch(server.url)
  if (!options) {
    router.push({ name: 'servers', query: { server: server.id } })
    return
  }
  try {
    await startServer(options, { url: server.url })
    router.push({ name: 'processes' })
  } catch (error) {
    fail(error)
  }
}

function refreshMenu() {
  installMenu({
    goTo: name => router.push({ name }),
    openDashboard,
    launchServer,
    servers: state.servers
  })
}

onMounted(async () => {
  await initialize()
  refreshMenu()
})

watch(() => state.servers.map(server => `${server.id}:${server.name}`).join('|'), refreshMenu)
</script>
