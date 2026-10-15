<template>
  <div class="min-h-screen bg-[#f7f7f7] text-[#000000] flex flex-col">
    <header class="sticky top-0 z-20 bg-[#f7f7f7]/85 backdrop-blur border-b border-gray-200/60">
      <!--
        Nothing but the mark: the sections, the dashboard included, are one
        Go menu away, with their accelerators, and the home page lists them
        again with the figures a navigation bar cannot show.
      -->
      <div class="max-w-5xl mx-auto px-5 h-14 flex items-center">
        <router-link to="/" class="lx-logo" title="Qibocal home" aria-label="Qibocal home">
          <launcher-logo />
        </router-link>
      </div>
    </header>

    <!-- Room for the status bar, so nothing hides behind it. -->
    <main class="flex-1 w-full pb-8">
      <router-view />
    </main>

    <status-bar />
    <closing-dialog />
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import ClosingDialog from './components/ClosingDialog.vue'
import LauncherLogo from './components/LauncherLogo.vue'
import StatusBar from './components/StatusBar.vue'
import { installMenu } from './menu.js'
import { state, fail, initialize, launchOptionsFor, openDashboard, startServer } from './state.js'

const router = useRouter()

/**
 * Bring a registered server up, as it was started last time or at its
 * registered address on this machine; one that is neither opens its form.
 */
async function launchServer(server) {
  const options = launchOptionsFor(server)
  if (!options) {
    router.push({ name: 'servers', query: { server: server.id } })
    return
  }
  try {
    await startServer(options, { url: server.url })
    router.push({ name: 'processes' })
  } catch (error) {
    fail(error, 'servers')
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
