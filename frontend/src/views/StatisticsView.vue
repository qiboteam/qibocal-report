<template>
  <div class="flex h-screen overflow-hidden bg-[#f7f7f7]">
    <!-- Left Sidebar -->
    <sidebar />

    <!-- Main Content Panel -->
    <main class="flex-1 flex flex-col min-w-0 overflow-y-auto">
      <!-- Top Bar: Header, Active Server info, Refresh -->
      <div class="sticky top-0 bg-[#f7f7f7]/90 backdrop-blur-md px-6 py-4 border-b border-gray-200/70 z-20 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-xl font-bold text-gray-900 tracking-tight">Statistics & Insights</h1>
            <span class="text-xs bg-purple-100 text-purple-800 font-semibold px-2 py-0.5 rounded-full">
              Overview
            </span>
          </div>
          <p class="text-xs text-gray-500 mt-0.5">
            Aggregated calibration metrics across platforms, protocols, authors, and tags. Click any metric to filter reports in the table view.
          </p>
        </div>

        <div class="flex items-center gap-3 shrink-0">
          <!-- Active Server Indicator -->
          <div
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs bg-white border border-gray-200 shadow-2xs"
            :title="activeServer?.url || 'Local Instance'"
          >
            <span
              class="w-2 h-2 rounded-full"
              :class="connectionError ? 'bg-red-500' : loading ? 'bg-amber-400 animate-pulse' : 'bg-emerald-500'"
            ></span>
            <span class="text-gray-400 text-[11px]">Server:</span>
            <span class="font-semibold text-gray-700 max-w-[140px] truncate">
              {{ activeServer?.name || 'Local Instance' }}
            </span>
          </div>

          <!-- Refresh Button -->
          <button
            @click="loadStats"
            :disabled="loading"
            class="px-3 py-1.5 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50"
            title="Refresh statistics"
          >
            <svg
              class="w-3.5 h-3.5"
              :class="loading ? 'animate-spin text-[#833dff]' : ''"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <!-- Content Area -->
      <div class="p-6 max-w-7xl w-full mx-auto space-y-6">
        <!-- Error Banner -->
        <div
          v-if="connectionError"
          class="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
        >
          <div>
            <div class="font-bold text-xs uppercase tracking-wider mb-0.5">Connection Error</div>
            <div class="text-xs">{{ connectionError }}</div>
          </div>
          <button
            @click="loadStats"
            class="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold transition cursor-pointer shrink-0"
          >
            Retry
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading && !stats" class="text-center py-20">
          <div class="inline-flex items-center gap-2 text-sm text-purple-700 font-medium">
            <svg class="animate-spin h-5 w-5 text-[#833dff]" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Computing statistics...</span>
          </div>
        </div>

        <template v-else>
          <!-- Top KPI Overview Cards -->
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
            <!-- Total Reports -->
            <div class="bm-card p-4 flex flex-col justify-between">
              <div class="flex items-center justify-between text-gray-500 mb-2">
                <span class="text-xs font-semibold uppercase tracking-wider">Reports</span>
                <span class="p-1.5 rounded-lg bg-purple-50 text-[#833dff]">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </span>
              </div>
              <div>
                <div class="text-2xl font-extrabold text-gray-900 font-mono">{{ totalReportsCount }}</div>
                <router-link
                  to="/dashboard"
                  class="text-[11px] text-[#833dff] hover:underline font-medium inline-flex items-center gap-0.5 mt-1"
                >
                  View all in table &rarr;
                </router-link>
              </div>
            </div>

            <!-- Platforms Count -->
            <div class="bm-card p-4 flex flex-col justify-between">
              <div class="flex items-center justify-between text-gray-500 mb-2">
                <span class="text-xs font-semibold uppercase tracking-wider">Platforms</span>
                <span class="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                </span>
              </div>
              <div>
                <div class="text-2xl font-extrabold text-gray-900 font-mono">{{ platformsList.length }}</div>
                <span class="text-[11px] text-gray-400">Unique QPUs / rigs</span>
              </div>
            </div>

            <!-- Protocols Count -->
            <div class="bm-card p-4 flex flex-col justify-between">
              <div class="flex items-center justify-between text-gray-500 mb-2">
                <span class="text-xs font-semibold uppercase tracking-wider">Protocols</span>
                <span class="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                </span>
              </div>
              <div>
                <div class="text-2xl font-extrabold text-gray-900 font-mono">{{ protocolsList.length }}</div>
                <span class="text-[11px] text-gray-400">Distinct routines</span>
              </div>
            </div>

            <!-- Authors Count -->
            <div class="bm-card p-4 flex flex-col justify-between">
              <div class="flex items-center justify-between text-gray-500 mb-2">
                <span class="text-xs font-semibold uppercase tracking-wider">Authors</span>
                <span class="p-1.5 rounded-lg bg-blue-50 text-blue-600">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </span>
              </div>
              <div>
                <div class="text-2xl font-extrabold text-gray-900 font-mono">{{ authorsList.length }}</div>
                <span class="text-[11px] text-gray-400">Contributors</span>
              </div>
            </div>

            <!-- Tags Count -->
            <div class="bm-card p-4 flex flex-col justify-between">
              <div class="flex items-center justify-between text-gray-500 mb-2">
                <span class="text-xs font-semibold uppercase tracking-wider">Tags</span>
                <span class="p-1.5 rounded-lg bg-amber-50 text-amber-600">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                </span>
              </div>
              <div>
                <div class="text-2xl font-extrabold text-gray-900 font-mono">{{ tagsList.length }}</div>
                <span class="text-[11px] text-gray-400">Applied labels</span>
              </div>
            </div>
          </div>

          <!-- Two Column Layout: Platforms and Authors -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Platform Breakdown Card -->
            <div class="bm-card p-5 flex flex-col">
              <div class="flex items-center justify-between pb-3 border-b border-gray-100 mb-3">
                <div class="flex items-center gap-2">
                  <div class="w-2.5 h-2.5 rounded-full bg-[#833dff]"></div>
                  <h2 class="text-sm font-bold text-gray-900 uppercase tracking-wider">Reports by Platform</h2>
                </div>
                <span class="text-xs text-gray-400 font-mono">{{ platformsList.length }} platforms</span>
              </div>

              <div v-if="platformsList.length === 0" class="py-8 text-center text-xs text-gray-400 italic">
                No platform data found
              </div>

              <div v-else class="space-y-3 flex-1 overflow-y-auto max-h-[380px] pr-1">
                <div
                  v-for="plat in platformsList"
                  :key="plat.name"
                  @click="filterBy('platform', plat.name)"
                  class="group p-2.5 rounded-xl hover:bg-purple-50/60 transition cursor-pointer border border-transparent hover:border-purple-100"
                  :title="`Filter table by platform: ${plat.name}`"
                >
                  <div class="flex items-center justify-between mb-1.5">
                    <div class="flex items-center gap-2 min-w-0">
                      <span class="font-mono text-xs font-semibold text-gray-800 group-hover:text-[#833dff] transition truncate">
                        {{ plat.name || 'Unknown' }}
                      </span>
                    </div>
                    <div class="flex items-center gap-2 shrink-0">
                      <span class="text-xs font-bold font-mono text-gray-900">{{ plat.count }}</span>
                      <span class="text-[11px] text-gray-400 font-mono">({{ getPercentage(plat.count, totalReportsCount) }}%)</span>
                      <span class="text-xs text-[#833dff] opacity-0 group-hover:opacity-100 transition ml-1 font-semibold">
                        &rarr;
                      </span>
                    </div>
                  </div>
                  <!-- Progress Bar -->
                  <div class="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div
                      class="bg-gradient-to-r from-[#833dff] to-purple-400 h-2 rounded-full transition-all duration-300"
                      :style="{ width: `${getPercentage(plat.count, totalReportsCount)}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Author Breakdown Card -->
            <div class="bm-card p-5 flex flex-col">
              <div class="flex items-center justify-between pb-3 border-b border-gray-100 mb-3">
                <div class="flex items-center gap-2">
                  <div class="w-2.5 h-2.5 rounded-full bg-blue-500"></div>
                  <h2 class="text-sm font-bold text-gray-900 uppercase tracking-wider">Reports by Author</h2>
                </div>
                <span class="text-xs text-gray-400 font-mono">{{ authorsList.length }} authors</span>
              </div>

              <div v-if="authorsList.length === 0" class="py-8 text-center text-xs text-gray-400 italic">
                No author data found
              </div>

              <div v-else class="space-y-3 flex-1 overflow-y-auto max-h-[380px] pr-1">
                <div
                  v-for="aut in authorsList"
                  :key="aut.name"
                  @click="filterBy('author', aut.name)"
                  class="group p-2.5 rounded-xl hover:bg-blue-50/60 transition cursor-pointer border border-transparent hover:border-blue-100"
                  :title="`Filter table by author: ${aut.name}`"
                >
                  <div class="flex items-center justify-between mb-1.5">
                    <div class="flex items-center gap-2.5 min-w-0">
                      <div class="w-6 h-6 rounded-full bg-blue-100 text-blue-700 font-bold text-[11px] flex items-center justify-center shrink-0 uppercase font-mono">
                        {{ aut.name[0] || '?' }}
                      </div>
                      <span class="text-xs font-semibold text-gray-800 group-hover:text-blue-700 transition truncate">
                        {{ aut.name || 'Unknown' }}
                      </span>
                    </div>
                    <div class="flex items-center gap-2 shrink-0">
                      <span class="text-xs font-bold font-mono text-gray-900">{{ aut.count }}</span>
                      <span class="text-[11px] text-gray-400 font-mono">({{ getPercentage(aut.count, totalReportsCount) }}%)</span>
                      <span class="text-xs text-blue-600 opacity-0 group-hover:opacity-100 transition ml-1 font-semibold">
                        &rarr;
                      </span>
                    </div>
                  </div>
                  <!-- Progress Bar -->
                  <div class="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div
                      class="bg-gradient-to-r from-blue-500 to-indigo-400 h-2 rounded-full transition-all duration-300"
                      :style="{ width: `${getPercentage(aut.count, totalReportsCount)}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Two Column Layout: Protocol Frequencies & Tags/Timeline -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Protocol Frequencies Card with Search -->
            <div class="bm-card p-5 flex flex-col">
              <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-gray-100 gap-2 mb-3">
                <div class="flex items-center gap-2">
                  <div class="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
                  <h2 class="text-sm font-bold text-gray-900 uppercase tracking-wider">Reports per Protocol</h2>
                </div>
                <!-- Protocol Search Filter -->
                <div class="relative max-w-xs w-full">
                  <input
                    v-model="protocolSearch"
                    type="text"
                    placeholder="Filter protocols..."
                    class="w-full text-xs px-2.5 py-1 bg-gray-50 border-0 rounded-lg focus:outline-none focus:ring-1 focus:ring-[#833dff]"
                  />
                </div>
              </div>

              <div v-if="filteredProtocols.length === 0" class="py-8 text-center text-xs text-gray-400 italic">
                {{ protocolSearch ? 'No matching protocols' : 'No protocol data found' }}
              </div>

              <div v-else class="space-y-2 flex-1 overflow-y-auto max-h-[400px] pr-1">
                <div
                  v-for="proto in filteredProtocols"
                  :key="proto.name"
                  @click="filterBy('protocol', proto.name)"
                  class="group p-2 rounded-xl hover:bg-emerald-50/60 transition cursor-pointer border border-transparent hover:border-emerald-100"
                  :title="`Filter table by protocol: ${proto.name}`"
                >
                  <div class="flex items-center justify-between mb-1">
                    <span class="font-mono text-xs font-semibold text-gray-800 group-hover:text-emerald-700 transition truncate mr-2">
                      {{ proto.name }}
                    </span>
                    <div class="flex items-center gap-2 shrink-0">
                      <span class="text-xs font-bold font-mono text-gray-900">{{ proto.count }}</span>
                      <span class="text-[10px] text-gray-400 font-mono">({{ getPercentage(proto.count, maxProtocolCount) }}% of max)</span>
                      <span class="text-xs text-emerald-600 opacity-0 group-hover:opacity-100 transition ml-1 font-semibold">
                        &rarr;
                      </span>
                    </div>
                  </div>
                  <div class="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      class="bg-gradient-to-r from-emerald-500 to-teal-400 h-1.5 rounded-full transition-all duration-300"
                      :style="{ width: `${getPercentage(proto.count, maxProtocolCount)}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tags & Activity Timeline Column -->
            <div class="space-y-6 flex flex-col">
              <!-- Tags & Labels Cloud Card -->
              <div class="bm-card p-5">
                <div class="flex items-center justify-between pb-3 border-b border-gray-100 mb-3">
                  <div class="flex items-center gap-2">
                    <div class="w-2.5 h-2.5 rounded-full bg-amber-500"></div>
                    <h2 class="text-sm font-bold text-gray-900 uppercase tracking-wider">Tags & Labels</h2>
                  </div>
                  <span class="text-xs text-gray-400 font-mono">{{ tagsList.length }} tags</span>
                </div>

                <div v-if="tagsList.length === 0" class="py-6 text-center text-xs text-gray-400 italic">
                  No tags or labels found
                </div>

                <div v-else class="flex flex-wrap gap-2">
                  <button
                    v-for="t in tagsList"
                    :key="t.name"
                    @click="filterBy('label', t.name)"
                    class="group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-50 hover:bg-[#833dff] text-purple-700 hover:text-white transition font-mono text-xs cursor-pointer select-none border-0 shadow-none"
                    :title="`Filter table by tag: ${t.name}`"
                  >
                    <span class="font-semibold">{{ t.name }}</span>
                    <span class="text-[10px] bg-white/70 group-hover:bg-white/20 group-hover:text-white px-1.5 py-0.2 rounded-full font-bold">
                      {{ t.count }}
                    </span>
                  </button>
                </div>
              </div>

              <!-- Date Activity Histogram Card -->
              <div class="bm-card p-5 flex-1 flex flex-col">
                <div class="flex items-center justify-between pb-3 border-b border-gray-100 mb-3">
                  <div class="flex items-center gap-2">
                    <div class="w-2.5 h-2.5 rounded-full bg-violet-500"></div>
                    <h2 class="text-sm font-bold text-gray-900 uppercase tracking-wider">Activity Over Time</h2>
                  </div>
                  <span class="text-xs text-gray-400 font-mono">{{ dateBins.length }} days</span>
                </div>

                <div v-if="dateBins.length === 0" class="py-6 text-center text-xs text-gray-400 italic">
                  No date history available
                </div>

                <div v-else class="flex-1 flex flex-col justify-end">
                  <div class="flex items-end gap-1.5 h-32 w-full pt-4 overflow-x-auto pb-1">
                    <div
                      v-for="bin in dateBins"
                      :key="bin.date"
                      @click="filterBy('date', bin.date)"
                      class="flex-1 min-w-[20px] max-w-[48px] flex flex-col items-center gap-1 group cursor-pointer"
                      :title="`${bin.date}: ${bin.count} report(s) - Click to filter`"
                    >
                      <span class="text-[9px] font-mono text-gray-400 opacity-0 group-hover:opacity-100 transition">
                        {{ bin.count }}
                      </span>
                      <div class="w-full bg-purple-100 group-hover:bg-purple-200 rounded-t transition-all duration-200 relative overflow-hidden h-full flex items-end">
                        <div
                          class="w-full bg-[#833dff] group-hover:bg-[#6c2bd9] rounded-t transition-all duration-300"
                          :style="{ height: `${Math.max(12, getPercentage(bin.count, maxDateCount))}%` }"
                        ></div>
                      </div>
                      <span class="text-[9px] font-mono text-gray-500 truncate w-full text-center">
                        {{ bin.date.slice(5) }}
                      </span>
                    </div>
                  </div>
                  <div class="text-[10px] text-gray-400 text-center mt-2 italic">
                    Click any day to filter table reports for that date
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { state, apiFetch, ensureServersLoaded } from '../store.js'
import Sidebar from '../components/Sidebar.vue'

const router = useRouter()

const stats = ref(null)
const loading = ref(true)
const connectionError = ref(null)
const protocolSearch = ref('')

const activeServer = computed(() => state.activeServer)

const totalReportsCount = computed(() => {
  if (stats.value?.total_reports !== undefined && stats.value?.total_reports > 0) return stats.value.total_reports
  if (stats.value?.platforms?.length) {
    return stats.value.platforms.reduce((sum, p) => sum + p.count, 0)
  }
  return 0
})

const platformsList = computed(() => {
  return stats.value?.platforms || []
})

const protocolsList = computed(() => {
  return stats.value?.protocols || []
})

const filteredProtocols = computed(() => {
  const all = protocolsList.value
  if (!protocolSearch.value.trim()) return all
  const q = protocolSearch.value.trim().toLowerCase()
  return all.filter(p => p.name.toLowerCase().includes(q))
})

const maxProtocolCount = computed(() => {
  const all = protocolsList.value
  if (!all.length) return 1
  return Math.max(...all.map(p => p.count), 1)
})

const authorsList = computed(() => {
  if (stats.value?.author_frequencies?.length) {
    return stats.value.author_frequencies
  }
  if (stats.value?.authors?.length) {
    return stats.value.authors.map(a => ({ name: a, count: 1 }))
  }
  return []
})

const tagsList = computed(() => {
  if (stats.value?.tag_frequencies?.length) {
    return stats.value.tag_frequencies
  }
  const tags = stats.value?.labels || stats.value?.tags || []
  return tags.map(t => ({ name: t, count: 1 }))
})

const dateBins = computed(() => {
  return stats.value?.date_histogram || []
})

const maxDateCount = computed(() => {
  const bins = dateBins.value
  if (!bins.length) return 1
  return Math.max(...bins.map(b => b.count), 1)
})

function getPercentage(count, total) {
  if (!total || total <= 0) return 0
  return Math.min(100, Math.round((count / total) * 100))
}

function filterBy(key, value) {
  if (!value) return
  router.push({
    path: '/dashboard',
    query: { [key]: value }
  })
}

async function loadStats() {
  loading.value = true
  connectionError.value = null
  try {
    const res = await apiFetch('/api/reports/stats')
    if (res.ok) {
      stats.value = await res.json()
      loading.value = false
    } else {
      connectionError.value = `Server returned status ${res.status}`
      loading.value = false
    }
  } catch (err) {
    connectionError.value = `Could not connect to ${activeServer.value?.name || 'server'}: ${err.message || 'Network error'}`
    loading.value = false
  }
}

onMounted(async () => {
  await ensureServersLoaded()
  await loadStats()
})

watch(
  () => [state.activeServer?.id, state.activeServer?.url],
  async ([newId, newUrl], [oldId, oldUrl]) => {
    if (newId !== oldId || newUrl !== oldUrl) {
      stats.value = null
      await loadStats()
    }
  }
)
</script>
