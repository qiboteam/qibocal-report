<template>
  <div class="max-w-5xl mx-auto px-5 py-10">
    <div class="text-center mb-9">
      <h1 class="text-2xl sm:text-3xl font-semibold text-gray-900 tracking-tight">
        Qibocal on this machine
      </h1>
      <p class="mt-1.5 text-xs sm:text-sm text-gray-500 max-w-xl mx-auto">
        Start report servers, open notebook sessions and browse your reports, without leaving the application.
      </p>
    </div>

    <!-- One size for every card: the grid stretches them, the descriptions are of a length. -->
    <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 items-stretch">
      <button
        type="button"
        class="bm-card text-left p-5 flex items-start gap-3.5 hover:-translate-y-px transition min-h-[6.5rem]"
        :class="{ 'lx-focus': focused(0) }"
        @click="openDashboard()"
      >
        <span class="w-9 h-9 rounded-xl bg-[#833dff] text-white inline-flex items-center justify-center shrink-0">
          <LayoutDashboard class="w-4.5 h-4.5" />
        </span>
        <span>
          <span class="block text-sm font-semibold text-gray-900">Dashboard</span>
          <span class="block mt-0.5 text-xs text-gray-500">
            Browse the reports, with every server the launcher knows already connected.
          </span>
        </span>
      </button>

      <router-link
        v-for="(section, index) in others"
        :key="section.name"
        :to="section.path"
        class="bm-card p-5 flex items-start gap-3.5 hover:-translate-y-px transition min-h-[6.5rem]"
        :class="{ 'lx-focus': focused(index + 1) }"
      >
        <span class="w-9 h-9 rounded-xl bg-[#ebe0ff] text-[#3b107e] inline-flex items-center justify-center shrink-0">
          <component :is="sectionIcons[section.icon]" class="w-4.5 h-4.5" />
        </span>
        <span>
          <span class="block text-sm font-semibold text-gray-900">
            {{ section.title }}
            <span v-if="badge(section.name)" class="ml-1.5 text-[11px] font-medium text-gray-400">
              {{ badge(section.name) }}
            </span>
          </span>
          <span class="block mt-0.5 text-xs text-gray-500">{{ section.summary }}</span>
        </span>
      </router-link>
    </div>

    <!--
      What runs right now, in a line each: the way to its card in Running,
      and the way to where it is used — the dashboard for a server, the
      browser for a notebook, Configuration for an installation.
    -->
    <section class="mt-8">
      <div class="flex items-center gap-2 px-1 mb-2">
        <h2 class="text-sm font-semibold text-gray-900">Running now</h2>
        <span v-if="live.length" class="text-xs text-gray-400">{{ live.length }}</span>
      </div>
      <p v-if="!live.length" class="px-1 text-xs text-gray-400">Nothing is running.</p>
      <div v-else class="bm-card divide-y divide-gray-100">
        <div v-for="process in live" :key="process.id" class="flex items-center gap-3 px-4 py-2.5">
          <span class="lx-dot" :class="process.status === 'running' ? 'bg-emerald-500' : 'bg-amber-500'" />
          <span class="min-w-0 flex-1">
            <span class="block text-xs font-medium text-gray-900 truncate">
              {{ process.label }}
              <span class="ml-1.5 text-[10px] uppercase tracking-wide text-gray-400 font-normal">{{ kindLabel(process) }}</span>
            </span>
            <span class="block lx-mono text-gray-500 truncate">{{ process.url || process.detail }}</span>
          </span>
          <router-link
            :to="{ name: 'processes', query: { process: process.id } }"
            class="lx-action"
            title="Its card in Running, with the output"
          >
            <Activity class="w-3.5 h-3.5" /> Running
          </router-link>
          <button
            v-if="process.kind === 'server' && process.url"
            type="button"
            class="lx-action"
            title="Read its reports in the dashboard"
            @click="openDashboard(process.url)"
          >
            <LayoutDashboard class="w-3.5 h-3.5" /> Dashboard
          </button>
          <button
            v-else-if="process.kind === 'notebook' && process.url"
            type="button"
            class="lx-action"
            title="Open the session in the browser"
            @click="openExternal(process.url)"
          >
            <ExternalLink class="w-3.5 h-3.5" /> Browser
          </button>
          <router-link
            v-else-if="process.kind === 'setup'"
            to="/settings"
            class="lx-action"
            title="The installation, in Configuration"
          >
            <Settings class="w-3.5 h-3.5" /> Configuration
          </router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Activity, ExternalLink, LayoutDashboard, Settings } from 'lucide-vue-next'
import { sections } from '../router.js'
import { sectionIcons } from '../icons.js'
import { openExternal } from '../bridge.js'
import { state, openDashboard } from '../state.js'
import { usePageKeys } from '../composables/pageKeys.js'

const router = useRouter()

/** The cards, in the order of use: what runs, then what to start. */
const ORDER = ['processes', 'servers', 'notebooks', 'settings', 'help']
const others = ORDER.map(name => sections.find(section => section.name === name)).filter(Boolean)

const running = computed(() => state.processes.filter(process => process.status === 'running').length)
const connections = computed(() => Object.keys(state.notebooks || {}).length)
/** Everything alive: running, or still being stopped. */
const live = computed(() => state.processes.filter(process => process.status === 'running' || process.status === 'stopping'))

function badge(name) {
  if (name === 'servers' && state.servers.length) return `${state.servers.length} registered`
  if (name === 'processes' && running.value) return `${running.value} running`
  if (name === 'notebooks' && connections.value) return `${connections.value} saved`
  return ''
}

function kindLabel(process) {
  if (process.kind === 'setup') return 'installation'
  return process.kind
}

// The keyboard walks the cards: the dashboard first, then the sections.
const { focused } = usePageKeys({
  page: 'home',
  count: () => others.length + 1,
  actions: {
    Enter: index => (index === 0 ? openDashboard() : router.push(others[index - 1].path))
  }
})
</script>
