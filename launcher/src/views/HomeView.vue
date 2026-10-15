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
        v-for="section in others"
        :key="section.name"
        :to="section.path"
        class="bm-card p-5 flex items-start gap-3.5 hover:-translate-y-px transition min-h-[6.5rem]"
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

  </div>
</template>

<script setup>
import { computed } from 'vue'
import { LayoutDashboard } from 'lucide-vue-next'
import { sections } from '../router.js'
import { sectionIcons } from '../icons.js'
import { state, openDashboard } from '../state.js'

const others = sections.filter(section => section.name !== 'home')

const running = computed(() => state.processes.filter(process => process.status === 'running').length)
const connections = computed(() => Object.keys(state.notebooks || {}).length)


function badge(name) {
  if (name === 'servers' && state.servers.length) return `${state.servers.length} registered`
  if (name === 'processes' && running.value) return `${running.value} running`
  if (name === 'notebooks' && connections.value) return `${connections.value} saved`
  return ''
}
</script>
