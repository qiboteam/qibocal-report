<template>
  <div class="bm-card p-4 sm:p-5 mb-5 transition-all animate-fade-in border border-purple-100/80 bg-white shadow-xs">
    <!-- Header: Title, Ratio Badge & Actions -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-gray-100">
      <div class="flex items-center gap-2.5 min-w-0">
        <div class="w-8 h-8 rounded-xl bg-purple-100 text-[#833dff] flex items-center justify-center font-bold text-sm shrink-0">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <div class="min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <h3 class="text-sm font-bold text-gray-900 tracking-tight">
              {{ isFiltered ? 'Filtered Calibration Summary' : 'Calibration Corpus Summary' }}
            </h3>
            <span
              v-if="isFiltered"
              class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-purple-100 text-purple-800 font-mono"
            >
              {{ totalFilteredReports }} / {{ totalFullReports }} reports ({{ filteredPercentage }}%)
            </span>
            <span
              v-else
              class="px-2 py-0.5 rounded-full text-[11px] font-medium bg-gray-100 text-gray-600 font-mono"
            >
              {{ totalFullReports }} reports total
            </span>
          </div>
          <p class="text-[11px] text-gray-400 truncate">
            {{ isFiltered ? 'InspireHEP-style aggregated statistics for current filter criteria' : 'Aggregated statistics across all calibration runs' }}
          </p>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="flex items-center gap-3 shrink-0 self-end sm:self-center">
        <button
          v-if="isFiltered"
          @click="$emit('reset-filters')"
          class="text-xs text-[#833dff] hover:underline font-semibold bg-transparent border-0 cursor-pointer p-0"
        >
          Reset filters
        </button>
        <button
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition cursor-pointer bg-transparent border-0"
          title="Hide statistics recap"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Key Metrics Banner (InspireHEP Stat Callouts) -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 my-3.5">
      <!-- Reports Tile -->
      <div class="bg-gray-50/90 p-2.5 rounded-xl border border-gray-100 flex flex-col justify-between">
        <span class="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Reports</span>
        <div class="flex items-baseline gap-1.5 mt-0.5">
          <span class="text-xl font-bold font-mono text-gray-900">{{ totalFilteredReports }}</span>
          <span v-if="isFiltered" class="text-[11px] font-mono text-gray-400">/ {{ totalFullReports }}</span>
        </div>
        <span v-if="isFiltered" class="text-[10px] text-purple-700 font-mono mt-0.5">{{ filteredPercentage }}% matched</span>
        <span v-else class="text-[10px] text-gray-400 mt-0.5">100% of dataset</span>
      </div>

      <!-- Protocols Tile -->
      <div class="bg-gray-50/90 p-2.5 rounded-xl border border-gray-100 flex flex-col justify-between">
        <span class="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Protocols</span>
        <div class="flex items-baseline gap-1.5 mt-0.5">
          <span class="text-xl font-bold font-mono text-emerald-600">{{ topProtocols.length }}</span>
        </div>
        <span class="text-[10px] text-gray-400 mt-0.5">unique routines</span>
      </div>

      <!-- Platforms Tile -->
      <div class="bg-gray-50/90 p-2.5 rounded-xl border border-gray-100 flex flex-col justify-between">
        <span class="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Platforms</span>
        <div class="flex items-baseline gap-1.5 mt-0.5">
          <span class="text-xl font-bold font-mono text-blue-600">{{ topPlatforms.length }}</span>
        </div>
        <span class="text-[10px] text-gray-400 mt-0.5">target architectures</span>
      </div>

      <!-- Authors Tile -->
      <div class="bg-gray-50/90 p-2.5 rounded-xl border border-gray-100 flex flex-col justify-between">
        <span class="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Authors</span>
        <div class="flex items-baseline gap-1.5 mt-0.5">
          <span class="text-xl font-bold font-mono text-amber-600">{{ topAuthors.length }}</span>
        </div>
        <span class="text-[10px] text-gray-400 mt-0.5">contributors</span>
      </div>
    </div>

    <!-- Structured Distribution Breakdown (InspireHEP Multi-column Blueprint) -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 pt-1">
      <!-- Column 1: Protocols Breakdown Table -->
      <div class="bg-gray-50/60 rounded-xl p-3 border border-gray-100 flex flex-col min-w-0">
        <div class="flex items-center justify-between pb-2 mb-2 border-b border-gray-200/60">
          <div class="flex items-center gap-1.5 min-w-0">
            <div class="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></div>
            <span class="text-xs font-bold text-gray-700 uppercase tracking-wider truncate">Protocols Breakdown</span>
          </div>
          <span class="text-[10px] text-gray-400 font-mono">{{ topProtocols.length }}</span>
        </div>

        <div v-if="topProtocols.length === 0" class="py-6 text-center text-xs text-gray-400 italic">
          No protocol data found
        </div>
        <div v-else class="space-y-1.5 max-h-48 overflow-y-auto pr-1">
          <div
            v-for="p in topProtocols"
            :key="p.name"
            @click="$emit('toggle-protocol', p.name)"
            class="group flex flex-col p-1.5 rounded-lg hover:bg-white transition cursor-pointer border border-transparent hover:border-emerald-100"
            :title="`Click to filter table by protocol: ${p.name}`"
          >
            <div class="flex items-center justify-between text-xs mb-1 min-w-0 gap-2">
              <span class="font-mono text-[11px] font-medium text-gray-800 group-hover:text-emerald-700 truncate min-w-0 flex-1">
                {{ p.name }}
              </span>
              <span class="font-mono text-[11px] font-bold text-gray-900 shrink-0">
                {{ p.count }}
              </span>
            </div>
            <div class="w-full bg-gray-200/70 rounded-full h-1 overflow-hidden">
              <div
                class="bg-gradient-to-r from-emerald-500 to-teal-400 h-1 rounded-full transition-all"
                :style="{ width: `${Math.max(4, (p.count / maxProtocolCount) * 100)}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Column 2: Platforms & Authors Breakdown -->
      <div class="flex flex-col gap-3 min-w-0">
        <!-- Platforms Table -->
        <div class="bg-gray-50/60 rounded-xl p-3 border border-gray-100 flex flex-col min-w-0 flex-1">
          <div class="flex items-center justify-between pb-2 mb-2 border-b border-gray-200/60">
            <div class="flex items-center gap-1.5 min-w-0">
              <div class="w-2 h-2 rounded-full bg-blue-500 shrink-0"></div>
              <span class="text-xs font-bold text-gray-700 uppercase tracking-wider truncate">Platforms</span>
            </div>
            <span class="text-[10px] text-gray-400 font-mono">{{ topPlatforms.length }}</span>
          </div>

          <div v-if="topPlatforms.length === 0" class="py-2 text-center text-xs text-gray-400 italic">No platforms</div>
          <div v-else class="space-y-1 max-h-24 overflow-y-auto pr-1">
            <div
              v-for="plat in topPlatforms"
              :key="plat.name"
              @click="$emit('filter-platform', plat.name)"
              class="group flex items-center justify-between p-1 rounded-lg hover:bg-white transition cursor-pointer text-xs min-w-0 border border-transparent hover:border-blue-100"
              :title="`Click to filter by platform: ${plat.name}`"
            >
              <span class="font-mono text-[11px] font-medium text-gray-800 group-hover:text-blue-700 truncate min-w-0 flex-1">
                {{ plat.name }}
              </span>
              <span class="font-mono text-[11px] font-semibold text-blue-700 bg-blue-50 px-1.5 py-0.2 rounded-full shrink-0 ml-2">
                {{ plat.count }}
              </span>
            </div>
          </div>
        </div>

        <!-- Authors Table -->
        <div class="bg-gray-50/60 rounded-xl p-3 border border-gray-100 flex flex-col min-w-0 flex-1">
          <div class="flex items-center justify-between pb-2 mb-2 border-b border-gray-200/60">
            <div class="flex items-center gap-1.5 min-w-0">
              <div class="w-2 h-2 rounded-full bg-amber-500 shrink-0"></div>
              <span class="text-xs font-bold text-gray-700 uppercase tracking-wider truncate">Authors</span>
            </div>
            <span class="text-[10px] text-gray-400 font-mono">{{ topAuthors.length }}</span>
          </div>

          <div v-if="topAuthors.length === 0" class="py-2 text-center text-xs text-gray-400 italic">No authors</div>
          <div v-else class="space-y-1 max-h-24 overflow-y-auto pr-1">
            <div
              v-for="auth in topAuthors"
              :key="auth.name"
              @click="$emit('filter-author', auth.name)"
              class="group flex items-center justify-between p-1 rounded-lg hover:bg-white transition cursor-pointer text-xs min-w-0 border border-transparent hover:border-amber-100"
              :title="`Click to filter by author: ${auth.name}`"
            >
              <span class="text-[11px] font-medium text-gray-800 group-hover:text-amber-700 truncate min-w-0 flex-1">
                {{ auth.name }}
              </span>
              <span class="font-mono text-[11px] font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded-full shrink-0 ml-2">
                {{ auth.count }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Column 3: Dual-Timeline Activity (Filtered vs Full Set) -->
      <div class="bg-gray-50/60 rounded-xl p-3 border border-gray-100 flex flex-col justify-between min-w-0">
        <div>
          <div class="flex items-center justify-between pb-2 mb-2 border-b border-gray-200/60">
            <div class="flex items-center gap-1.5 min-w-0">
              <div class="w-2 h-2 rounded-full bg-violet-500 shrink-0"></div>
              <span class="text-xs font-bold text-gray-700 uppercase tracking-wider truncate">Activity Timeline</span>
            </div>
            <span v-if="isFiltered" class="text-[10px] text-purple-700 font-mono bg-purple-100 px-1.5 py-0.2 rounded shrink-0">
              Filtered vs Full
            </span>
          </div>

          <!-- Dual-bar DateHistogram -->
          <date-histogram
            :histogram="filterStats?.date_histogram"
            :full-histogram="fullStats?.date_histogram"
            :is-filtered="isFiltered"
            :show-title="false"
            height-class="h-28"
            @select-date="d => $emit('select-date', d)"
          />
        </div>

        <div class="text-[10px] text-gray-400 text-center mt-2 italic">
          {{ isFiltered ? 'Purple shows filtered reports; grey shows full dataset. Click bar to filter.' : 'Click any day bar to filter reports for that date.' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DateHistogram from './DateHistogram.vue'

const props = defineProps({
  filterStats: { type: Object, default: () => ({}) },
  fullStats: { type: Object, default: () => ({}) },
  isFiltered: { type: Boolean, default: false }
})

defineEmits([
  'toggle-protocol',
  'filter-platform',
  'filter-author',
  'select-date',
  'reset-filters',
  'close'
])

const totalFilteredReports = computed(() => {
  return props.filterStats?.total_reports ?? 0
})

const totalFullReports = computed(() => {
  return props.fullStats?.total_reports ?? props.filterStats?.total_reports ?? 0
})

const filteredPercentage = computed(() => {
  if (!props.isFiltered || totalFullReports.value === 0) return 100
  return ((totalFilteredReports.value / totalFullReports.value) * 100).toFixed(1)
})

const topProtocols = computed(() => {
  return props.filterStats?.protocols || []
})

const topPlatforms = computed(() => {
  return props.filterStats?.platforms || []
})

const topAuthors = computed(() => {
  return props.filterStats?.author_frequencies || []
})

const maxProtocolCount = computed(() => {
  const protos = props.filterStats?.protocols || []
  if (protos.length === 0) return 1
  return Math.max(...protos.map(p => p.count), 1)
})
</script>
