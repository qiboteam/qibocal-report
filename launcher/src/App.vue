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
      The status bar: the page's own colour, no edge, always on top, so it
      blends into a page that fits the window and sits over one that does
      not. The command line's version on the left; on the right, the latest
      thing said, fading by itself, and the count of everything said, which
      opens the list. An installation in progress sits between the two for
      as long as it runs, with the way to its output.
    -->
    <footer class="lx-status" role="status" aria-live="polite">
      <div class="px-5 h-full flex items-center gap-5">
        <router-link to="/settings" class="truncate shrink-0 max-w-[40%] hover:text-[#3b107e] transition" :title="versionTitle">
          {{ versionLabel }}
        </router-link>

        <router-link
          v-if="installing"
          to="/processes"
          class="inline-flex items-center gap-1.5 shrink-0 hover:text-[#3b107e] transition"
          title="Follow the installation in Running"
        >
          <Loader2 class="w-3 h-3 lx-spin" />
          Installing qibocal-report… follow it in Running
        </router-link>

        <div class="ml-auto flex items-center gap-2 min-w-0 relative">
          <span
            v-if="state.message"
            class="truncate"
            :class="state.message.kind === 'error' ? 'lx-status-error' : ''"
            :title="state.message.text"
          >{{ state.message.text }}</span>

          <button
            v-if="state.notifications.length"
            type="button"
            class="lx-count"
            :class="{ 'is-open': open }"
            :title="`${state.notifications.length} notification${state.notifications.length === 1 ? '' : 's'}`"
            :aria-expanded="open"
            @click="open = !open"
          >
            <Bell class="w-3 h-3" />
            <span class="lx-count-badge">{{ state.notifications.length }}</span>
          </button>

          <div v-if="open && state.notifications.length" class="lx-notices" role="list">
            <div class="lx-notices-head">
              <span>Notifications</span>
              <button type="button" class="hover:text-[#3b107e]" @click="clearAll">Clear all</button>
            </div>
            <div
              v-for="entry in state.notifications"
              :key="entry.id"
              class="lx-notice"
              :class="{ 'is-error': entry.kind === 'error' }"
              role="listitem"
            >
              <span class="lx-notice-time">{{ time(entry.at) }}</span>
              <span class="lx-notice-text">{{ entry.text }}</span>
              <button type="button" class="lx-notice-close" :aria-label="`Dismiss: ${entry.text}`" @click="dismissNotification(entry.id)">
                <X class="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, Loader2, X } from 'lucide-vue-next'
import LauncherLogo from './components/LauncherLogo.vue'
import { installMenu } from './menu.js'
import {
  state,
  dismiss,
  dismissNotification,
  fail,
  hasQibocal,
  initialize,
  installing,
  openDashboard,
  recallLaunch,
  startServer
} from './state.js'
import { describeSpec } from './lib/versions.js'

const router = useRouter()
const open = ref(false)

/** What the command line says of itself, with the version the launcher put there. */
const versionLabel = computed(() => {
  const environment = state.environment
  if (!environment) return ''
  if (!hasQibocal.value) return installing.value ? 'qibocal-report: installing' : 'qibocal-report not installed'
  const version = String(environment.version || '').replace(/^qibocal,?\s*version\s*/i, '').trim()
  const held = environment.source === 'managed' && environment.managedPackage
    ? describeSpec(environment.managedPackage, environment)
    : ''
  return `qibocal-report ${version || ''}${held ? ` · ${held}` : ''}`.replace(/\s+/g, ' ').trim()
})
const versionTitle = computed(() => state.environment?.executable || 'Configuration')

function time(at) {
  return new Date(at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function clearAll() {
  dismiss()
  open.value = false
}

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
// The list closes with its last entry, and when leaving the page.
watch(() => state.notifications.length, count => {
  if (!count) open.value = false
})
watch(() => router.currentRoute.value.fullPath, () => {
  open.value = false
})
</script>
