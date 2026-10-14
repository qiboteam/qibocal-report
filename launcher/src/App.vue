<template>
  <div class="min-h-screen bg-[#f7f7f7] text-[#000000] flex flex-col">
    <header class="sticky top-0 z-20 bg-[#f7f7f7]/85 backdrop-blur border-b border-gray-200/60">
      <!--
        Nothing but the mark and the dashboard: the sections are one Go menu
        away, with their accelerators, and the home page lists them again
        with the figures a navigation bar cannot show.
      -->
      <div class="max-w-5xl mx-auto px-5 h-14 flex items-center">
        <router-link to="/" class="lx-logo" title="Qibocal home" aria-label="Qibocal home">
          <launcher-logo />
        </router-link>

        <button
          type="button"
          class="ml-auto px-3 py-1.5 rounded-lg text-xs font-medium bg-[#833dff] text-white hover:bg-[#722ce6] active:scale-[0.98] transition shadow-2xs"
          @click="openDashboard()"
        >
          Dashboard
        </button>
      </div>
    </header>

    <!-- Room for the status bar, so nothing hides behind it. -->
    <main class="flex-1 w-full pb-8">
      <router-view />
    </main>

    <!--
      The status bar: one quiet line, always there, so a message never moves
      the page. What the launcher has to say appears on the left and fades
      by itself; an installation in progress sits on the right for as long
      as it runs, with the way to its output.
    -->
    <footer class="lx-status" role="status" aria-live="polite">
      <div class="max-w-5xl mx-auto px-5 h-full flex items-center gap-4">
        <span
          v-if="state.message"
          class="truncate"
          :class="state.message.kind === 'error' ? 'lx-status-error' : ''"
          :title="state.message.text"
          @click="dismiss"
        >{{ state.message.text }}</span>
        <router-link
          v-if="installing"
          to="/processes"
          class="ml-auto inline-flex items-center gap-1.5 shrink-0 hover:text-[#3b107e] transition"
          title="Follow the installation in Running"
        >
          <Loader2 class="w-3 h-3 lx-spin" />
          Installing qibocal-report… follow it in Running
        </router-link>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Loader2 } from 'lucide-vue-next'
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
