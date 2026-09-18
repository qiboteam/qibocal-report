<template>
  <div class="bm-card p-4 sm:p-5 mb-4 transition-all animate-fade-in border border-purple-100/80 bg-white shadow-xs">
    <!-- Header: Scope Toggle (only shown when selection is active) -->
    <div
      v-if="selectedCount > 0"
      class="flex items-center justify-between gap-3 pb-2 mb-3 border-b border-gray-100"
    >
      <div>
        <!-- Segmented scope switch (when checkboxes are selected and filters are active) -->
        <div
          v-if="isFiltered"
          class="inline-flex items-center bg-gray-100 p-0.5 rounded-lg text-xs"
        >
          <button
            @click="scopeMode = 'filtered'"
            class="px-2.5 py-0.5 rounded-md font-medium transition cursor-pointer"
            :class="scopeMode === 'filtered' ? 'bg-white text-purple-900 shadow-2xs font-semibold' : 'text-gray-500 hover:text-gray-800'"
          >
            Filtered ({{ totalFilteredReports }})
          </button>
          <button
            @click="scopeMode = 'selected'"
            class="px-2.5 py-0.5 rounded-md font-medium transition cursor-pointer"
            :class="scopeMode === 'selected' ? 'bg-white text-purple-900 shadow-2xs font-semibold' : 'text-gray-500 hover:text-gray-800'"
          >
            Selected ({{ selectedCount }})
          </button>
        </div>
        <span
          v-else
          class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-purple-50 text-purple-800"
        >
          Selected ({{ selectedCount }})
        </span>
      </div>
    </div>

    <!-- Key Metrics Banner (InspireHEP Stat Callouts) -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-3.5">
      <!-- Reports Tile -->
      <div class="bg-gray-50/90 p-2.5 rounded-xl border border-gray-100 flex flex-col justify-between">
        <span class="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Reports</span>
        <div class="flex items-baseline gap-1.5 mt-0.5">
          <span class="text-xl font-bold font-mono text-gray-900">{{ activeReportCount }}</span>
          <span v-if="isEffectiveFiltered" class="text-[11px] font-mono text-gray-400">/ {{ totalFullReports }}</span>
        </div>
        <span v-if="isEffectiveFiltered" class="text-[10px] text-purple-700 font-mono mt-0.5">{{ activePercentage }}% matched</span>
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

    <!-- Structured Distribution Breakdown (InspireHEP 2-column Blueprint) -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-1">
      <!-- Column 1: Protocols Breakdown Table -->
      <div class="bg-gray-50/60 rounded-xl p-3.5 border border-gray-100 flex flex-col min-w-0">
        <div class="flex items-center justify-between pb-2 mb-2 border-b border-gray-200/60">
          <div class="flex items-center gap-1.5 min-w-0">
            <div class="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></div>
            <span class="text-xs font-bold text-gray-700 uppercase tracking-wider truncate">Protocols Breakdown</span>
          </div>
          <span class="text-[10px] text-gray-400 font-mono">{{ topProtocols.length }} protocols</span>
        </div>

        <div v-if="topProtocols.length === 0" class="py-8 text-center text-xs text-gray-400 italic">
          No protocol data found
        </div>
        <div v-else class="space-y-1.5 max-h-52 overflow-y-auto pr-1">
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

          <div v-if="topPlatforms.length === 0" class="py-3 text-center text-xs text-gray-400 italic">No platforms</div>
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

          <div v-if="topAuthors.length === 0" class="py-3 text-center text-xs text-gray-400 italic">No authors</div>
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
    </div>

    <!-- Active Filter Pills at the bottom of summary -->
    <div
      v-if="hasAnyFilter"
      class="mt-3.5 pt-3 border-t border-gray-100 flex flex-wrap items-center gap-1.5"
    >
      <span class="text-[11px] text-gray-400 font-medium">Active Filters:</span>
      <span
        v-if="filters.author"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800"
      >
        Author: {{ filters.author }}
        <button
          type="button"
          @click="$emit('clear-filter', 'author')"
          class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-black cursor-pointer leading-none ml-0.5"
          title="Clear author filter"
        >&times;</button>
      </span>
      <span
        v-if="filters.platform"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
      >
        Platform: {{ filters.platform }}
        <button
          type="button"
          @click="$emit('clear-filter', 'platform')"
          class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-black cursor-pointer leading-none ml-0.5"
          title="Clear platform filter"
        >&times;</button>
      </span>
      <span
        v-for="p in filters.protocols"
        :key="p"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
      >
        {{ p }}
        <button
          type="button"
          @click="$emit('clear-filter', 'protocol', p)"
          class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-black cursor-pointer leading-none ml-0.5"
          title="Clear protocol filter"
        >&times;</button>
      </span>
      <span
        v-for="l in filters.labels"
        :key="l"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
      >
        Tag: {{ l }}
        <button
          type="button"
          @click="$emit('clear-filter', 'label', l)"
          class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-black cursor-pointer leading-none ml-0.5"
          title="Clear tag filter"
        >&times;</button>
      </span>
      <span
        v-if="filters.date"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
      >
        Date: {{ filters.date }}
        <button
          type="button"
          @click="$emit('clear-filter', 'date')"
          class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-black cursor-pointer leading-none ml-0.5"
          title="Clear date filter"
        >&times;</button>
      </span>
      <span
        v-if="filters.q && filters.q.trim()"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
      >
        Search: "{{ filters.q }}"
        <button
          type="button"
          @click="$emit('clear-filter', 'q')"
          class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-black cursor-pointer leading-none ml-0.5"
          title="Clear search query"
        >&times;</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { computeStatsFromReports } from '../utils/stats.js'

const props = defineProps({
  filterStats: { type: Object, default: () => ({}) },
  fullStats: { type: Object, default: () => ({}) },
  isFiltered: { type: Boolean, default: false },
  selectedCount: { type: Number, default: 0 },
  selectedReports: { type: Array, default: () => [] },
  filters: { type: Object, default: () => ({}) }
})

defineEmits([
  'toggle-protocol',
  'filter-platform',
  'filter-author',
  'clear-filter'
])

const hasAnyFilter = computed(() => {
  const f = props.filters || {}
  return Boolean(
    f.author ||
    f.platform ||
    (f.protocols && f.protocols.length > 0) ||
    (f.labels && f.labels.length > 0) ||
    f.date ||
    (f.q && f.q.trim())
  )
})

const scopeMode = ref('filtered')

const selectedStats = computed(() => {
  if (!props.selectedReports || props.selectedReports.length === 0) return null
  return computeStatsFromReports(props.selectedReports)
})

const isShowingSelected = computed(() => {
  if (props.selectedCount > 0) {
    if (!props.isFiltered) return true
    return scopeMode.value === 'selected'
  }
  return false
})

const activeStats = computed(() => {
  if (isShowingSelected.value && selectedStats.value) {
    return selectedStats.value
  }
  return props.filterStats || props.fullStats || {}
})

const isEffectiveFiltered = computed(() => {
  return props.isFiltered || isShowingSelected.value
})


const activeReportCount = computed(() => {
  return activeStats.value?.total_reports ?? 0
})

const totalFilteredReports = computed(() => {
  return props.filterStats?.total_reports ?? 0
})

const totalFullReports = computed(() => {
  return props.fullStats?.total_reports ?? props.filterStats?.total_reports ?? 0
})

const activePercentage = computed(() => {
  if (!isEffectiveFiltered.value || totalFullReports.value === 0) return 100
  return ((activeReportCount.value / totalFullReports.value) * 100).toFixed(1)
})

const topProtocols = computed(() => {
  return activeStats.value?.protocols || []
})

const topPlatforms = computed(() => {
  return activeStats.value?.platforms || []
})

const topAuthors = computed(() => {
  return activeStats.value?.author_frequencies || []
})

const maxProtocolCount = computed(() => {
  const protos = activeStats.value?.protocols || []
  if (protos.length === 0) return 1
  return Math.max(...protos.map(p => p.count), 1)
})
</script>
