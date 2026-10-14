<template>
  <div class="min-h-screen bg-[#f7f7f7] text-[#000000] flex flex-col">
    <header class="sticky top-0 z-20 bg-[#f7f7f7]/85 backdrop-blur border-b border-gray-200/60">
      <div class="max-w-5xl mx-auto px-5 h-14 flex items-center gap-4">
        <router-link to="/" class="flex items-center gap-2 shrink-0">
          <span class="w-6 h-6 rounded-lg bg-[#833dff] inline-flex items-center justify-center">
            <span class="w-2 h-2 rounded-full bg-white/90" />
          </span>
          <span class="text-sm font-semibold tracking-tight text-gray-900">Qibocal Launcher</span>
        </router-link>

        <nav class="flex items-center gap-0.5 ml-2 overflow-x-auto">
          <router-link
            v-for="section in sections"
            :key="section.name"
            :to="section.path"
            class="px-2.5 py-1.5 rounded-lg text-xs font-medium transition shrink-0"
            :class="route.name === section.name
              ? 'bg-white text-[#833dff] shadow-2xs'
              : 'text-gray-500 hover:text-gray-900'"
          >
            {{ section.title }}
            <span
              v-if="section.name === 'processes' && runningCount"
              class="ml-1 px-1.5 rounded-full bg-[#ebe0ff] text-[#3b107e] text-[10px] font-semibold"
            >{{ runningCount }}</span>
          </router-link>
        </nav>

        <div class="ml-auto flex items-center gap-2 shrink-0">
          <span
            class="hidden sm:inline-flex items-center gap-1.5 text-[11px] text-gray-500"
            :title="environmentTitle"
          >
            <span class="w-1.5 h-1.5 rounded-full" :class="hasQibocal ? 'bg-emerald-500' : 'bg-amber-500'" />
            {{ hasQibocal ? (state.environment?.version || 'qibocal ready') : 'qibocal not found' }}
          </span>
          <button
            type="button"
            class="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#833dff] text-white hover:bg-[#722ce6] active:scale-[0.98] transition shadow-2xs"
            @click="openDashboard()"
          >
            Dashboard
          </button>
        </div>
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
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { X } from 'lucide-vue-next'
import { sections } from './router.js'
import { installMenu } from './menu.js'
import {
  state,
  hasQibocal,
  dismiss,
  fail,
  initialize,
  openDashboard,
  recallLaunch,
  startServer
} from './state.js'

const route = useRoute()
const router = useRouter()

const runningCount = computed(() => state.processes.filter(process => process.status === 'running').length)
const environmentTitle = computed(() => {
  const environment = state.environment
  if (!environment?.executable) return 'Pick the Qibocal installation in the Configuration section.'
  return `${environment.executable}\nfound through ${environment.source}`
})

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
