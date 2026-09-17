<template>
  <aside
    class="no-print h-screen bg-white border-r border-gray-200/80 flex flex-col transition-all duration-300 z-30 shrink-0"
    :class="isCollapsed ? 'w-16' : 'w-72'"
  >
    <!-- Top Header: Server Switcher & Collapse Toggle -->
    <div class="p-3 border-b border-gray-100 flex items-center justify-between gap-2">
      <div v-if="!isCollapsed" class="flex-1 min-w-0">
        <!-- Quick Switch between registered servers (Issue #3) -->
        <div class="relative">
          <button
            @click="serverDropdownOpen = !serverDropdownOpen"
            class="w-full flex items-center justify-between p-2 rounded-xl bg-gray-50 hover:bg-purple-50 text-left transition border border-gray-100"
          >
            <div class="flex items-center gap-2 truncate">
              <div class="w-6 h-6 rounded-md bg-white p-0.5 shrink-0 shadow-xs" v-html="renderAvatar(activeServer?.avatar || 'quantum-ring')"></div>
              <span class="text-xs font-bold text-gray-800 truncate">{{ activeServer?.name || 'Select Server' }}</span>
            </div>
            <svg class="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Dropdown -->
          <div
            v-if="serverDropdownOpen"
            class="absolute top-full left-0 mt-1 w-full bg-white rounded-xl shadow-xl border border-gray-100 py-1.5 z-50 text-xs"
          >
            <div class="px-3 py-1 font-semibold text-gray-400 uppercase text-[10px]">Registered Servers</div>
            <div
              v-for="s in servers"
              :key="s.id"
              @click="switchServer(s)"
              class="px-3 py-2 hover:bg-purple-50 cursor-pointer flex items-center justify-between gap-2"
              :class="s.id === activeServer?.id ? 'bg-purple-50/60 font-bold text-[#833dff]' : 'text-gray-700'"
            >
              <div class="truncate">
                <div class="truncate">{{ s.name }}</div>
                <div class="text-[10px] font-mono text-gray-400 truncate">{{ s.url }}</div>
              </div>
              <span v-if="s.id === activeServer?.id" class="w-1.5 h-1.5 rounded-full bg-[#833dff] shrink-0"></span>
            </div>
            <div class="border-t border-gray-100 mt-1 pt-1">
              <router-link
                to="/servers"
                @click="serverDropdownOpen = false"
                class="px-3 py-1.5 text-[#833dff] hover:bg-purple-50 flex items-center gap-1.5 font-medium block"
              >
                + Manage Servers...
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- Collapse / Expand Button -->
      <button
        @click="isCollapsed = !isCollapsed"
        class="p-2 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition shrink-0"
        :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path v-if="!isCollapsed" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <!-- UPPER HALF: Navigation & History (Issue #3) -->
    <div class="h-1/2 overflow-y-auto p-3 flex flex-col justify-between border-b border-gray-200/80">
      <div class="space-y-1">
        <!-- Search Page -->
        <router-link
          to="/dashboard"
          class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition"
          :class="$route.path === '/dashboard' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100'"
        >
          <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span v-if="!isCollapsed">Search & Browse</span>
        </router-link>

        <!-- Current Report -->
        <router-link
          v-if="currentReportId"
          :to="`/reports/${currentReportId}`"
          class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition"
          :class="$route.path.startsWith('/reports') ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100'"
        >
          <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <span v-if="!isCollapsed" class="truncate">Current Report</span>
        </router-link>

        <!-- Collapsible Opened Reports History (Issue #3) -->
        <div v-if="!isCollapsed" class="pt-2">
          <button
            @click="historyOpen = !historyOpen"
            class="w-full flex items-center justify-between text-[11px] font-bold text-gray-400 uppercase tracking-wider px-3 py-1 hover:text-gray-600"
          >
            <span>Recent History</span>
            <svg class="w-3.5 h-3.5 transition" :class="historyOpen ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div v-if="historyOpen" class="mt-1 space-y-0.5 max-h-36 overflow-y-auto">
            <div
              v-if="history.length === 0"
              class="px-3 py-1 text-[11px] text-gray-400 italic"
            >
              No reports viewed yet
            </div>
            <router-link
              v-for="h in history"
              :key="h.id"
              :to="`/reports/${h.id}`"
              class="block px-3 py-1.5 rounded-lg text-xs hover:bg-gray-100 transition truncate"
              :class="$route.params.id === h.id ? 'text-[#833dff] font-semibold bg-purple-50' : 'text-gray-600'"
              :title="h.title"
            >
              <div class="truncate">{{ h.title }}</div>
              <div class="text-[10px] text-gray-400 font-mono">{{ h.date }}</div>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Docs Button (Issue #12) -->
      <div v-if="!isCollapsed" class="pt-2 border-t border-gray-100">
        <router-link
          to="/docs"
          class="flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition"
        >
          <svg class="w-4 h-4 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          Documentation
        </router-link>
      </div>
    </div>

    <!-- LOWER HALF: Page Dependent (Filters on Search, Protocols on Report) (Issue #3) -->
    <div v-if="!isCollapsed" class="h-1/2 overflow-y-auto p-3.5 flex flex-col">
      <!-- Context A: Search Filters -->
      <div v-if="isSearchMode">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-bold uppercase tracking-wider text-gray-800">Filters</span>
          <button
            @click="$emit('reset-filters')"
            class="text-[11px] text-[#833dff] hover:underline font-semibold"
          >
            Clear All
          </button>
        </div>

        <!-- Date Range & Histogram (Issue #3) -->
        <div class="mb-4">
          <date-histogram
            :histogram="filterStats?.date_histogram"
            @select-date="d => $emit('update-filter', { key: 'date', value: d })"
          />
        </div>

        <!-- Author Filter -->
        <div class="mb-4">
          <label class="block text-xs font-semibold text-gray-700 mb-1">Author</label>
          <select
            :value="selectedAuthor"
            @change="$emit('update-filter', { key: 'author', value: $event.target.value })"
            class="w-full text-xs p-2 rounded-lg bg-gray-50 border border-gray-200 focus:outline-none focus:ring-1 focus:ring-[#833dff]"
          >
            <option value="">All Authors</option>
            <option v-for="a in filterStats?.authors" :key="a" :value="a">{{ a }}</option>
          </select>
        </div>

        <!-- Protocols Checklist (sorted by frequency from most to least, Issue #3) -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-1.5">
            <label class="text-xs font-semibold text-gray-700">Protocols</label>
            <span class="text-[10px] text-gray-400">By frequency</span>
          </div>
          <div class="space-y-1.5 max-h-36 overflow-y-auto pr-1">
            <label
              v-for="p in filterStats?.protocols"
              :key="p.name"
              class="flex items-center justify-between text-xs text-gray-700 hover:bg-gray-50 p-1 rounded cursor-pointer"
            >
              <div class="flex items-center gap-2 truncate">
                <input
                  type="checkbox"
                  :value="p.name"
                  :checked="selectedProtocols.includes(p.name)"
                  @change="$emit('toggle-protocol', p.name)"
                  class="rounded text-[#833dff] focus:ring-[#833dff] h-3.5 w-3.5"
                />
                <span class="truncate font-mono text-[11px]">{{ p.name }}</span>
              </div>
              <span class="text-[10px] font-semibold text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded-full">
                {{ p.count }}
              </span>
            </label>
          </div>
        </div>

        <!-- Labels / Tags Checklist with Search (Issue #3) -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1">Labels</label>
          <input
            v-model="labelSearch"
            placeholder="Filter labels..."
            class="w-full text-xs px-2.5 py-1 mb-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none"
          />
          <div class="space-y-1 max-h-24 overflow-y-auto">
            <label
              v-for="lab in filteredLabels"
              :key="lab"
              class="flex items-center gap-2 text-xs text-gray-700 hover:bg-gray-50 p-1 rounded cursor-pointer"
            >
              <input
                type="checkbox"
                :value="lab"
                :checked="selectedLabels.includes(lab)"
                @change="$emit('toggle-label', lab)"
                class="rounded text-[#833dff] focus:ring-[#833dff] h-3.5 w-3.5"
              />
              <span class="text-xs">#{{ lab }}</span>
            </label>
          </div>
        </div>
      </div>

      <!-- Context B: Protocols Summary on Report View (Issue #3, #10) -->
      <div v-else-if="isReportMode">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-bold uppercase tracking-wider text-gray-800">Protocols Summary</span>
          <span class="text-[11px] text-purple-700 font-mono bg-purple-100 px-1.5 py-0.5 rounded">
            {{ reportProtocols?.length || 0 }} routines
          </span>
        </div>

        <div class="space-y-1.5 overflow-y-auto flex-1">
          <a
            v-for="p in reportProtocols"
            :key="p.id"
            @click.prevent="scrollToProtocol(p.id)"
            class="block p-2 rounded-xl text-xs hover:bg-purple-50/70 border border-gray-100 hover:border-purple-200 transition group cursor-pointer"
          >
            <div class="flex items-center justify-between">
              <span class="font-semibold text-gray-800 group-hover:text-[#833dff] truncate">{{ p.name }}</span>
              <span class="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 rounded">✓</span>
            </div>
            <div class="flex items-center justify-between text-[10px] text-gray-400 mt-1 font-mono">
              <span>{{ p.execution_time || 'N/A' }}</span>
              <span>{{ p.num_figures || (p.figures ? p.figures.length : 0) }} plots</span>
            </div>
          </a>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { state, setActiveServer } from '../store.js'
import { renderAvatar } from './Avatars.js'
import DateHistogram from './DateHistogram.vue'

const props = defineProps({
  filterStats: { type: Object, default: () => ({}) },
  selectedAuthor: { type: String, default: '' },
  selectedProtocols: { type: Array, default: () => [] },
  selectedLabels: { type: Array, default: () => [] },
  reportProtocols: { type: Array, default: () => [] }
})

defineEmits(['update-filter', 'reset-filters', 'toggle-protocol', 'toggle-label'])

const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)
const serverDropdownOpen = ref(false)
const historyOpen = ref(true)
const labelSearch = ref('')

const servers = computed(() => state.servers)
const activeServer = computed(() => state.activeServer)
const history = computed(() => state.history)
const currentReportId = computed(() => state.currentReportId)

const isSearchMode = computed(() => route.path === '/dashboard')
const isReportMode = computed(() => route.path.startsWith('/reports/'))

const filteredLabels = computed(() => {
  const all = props.filterStats?.labels || []
  if (!labelSearch.value) return all
  return all.filter(l => l.toLowerCase().includes(labelSearch.value.toLowerCase()))
})

function switchServer(s) {
  setActiveServer(s)
  serverDropdownOpen.value = false
  if (route.path !== '/dashboard') {
    router.push('/dashboard')
  }
}

function scrollToProtocol(id) {
  const el = document.getElementById(`proto-${id}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}
</script>
