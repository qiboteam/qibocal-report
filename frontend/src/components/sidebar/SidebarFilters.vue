<template>
  <div v-if="!isCollapsed" class="w-full min-w-0">
    <!-- Filters Header -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-bold uppercase tracking-wider text-gray-800">Filters</span>
      <button
        @click="$emit('reset-filters')"
        class="text-[11px] text-[#833dff] hover:underline font-semibold cursor-pointer shrink-0 bg-transparent hover:bg-transparent border-0 shadow-none p-0"
      >
        Clear All
      </button>
    </div>

    <!-- Date Range & Histogram -->
    <div class="mb-4 w-full min-w-0 overflow-hidden">
      <date-histogram
        :histogram="filterStats?.date_histogram"
        :full-histogram="fullStats?.date_histogram"
        :is-filtered="isFiltered"
        :start-date="selectedStartDate"
        :end-date="selectedEndDate"
        :selected-date="selectedDate"
        @select-range="range => $emit('update-filter', { key: 'dateRange', ...range })"
        @select-date="d => $emit('update-filter', { key: 'date', value: d })"
        @clear-range="$emit('update-filter', { key: 'dateRange', startDate: '', endDate: '' })"
      />
    </div>

    <!-- Tags Checklist with Search -->
    <div class="mb-4 w-full min-w-0">
      <label class="block text-xs font-semibold text-gray-700 mb-1">Tags</label>
      <input
        v-model="labelSearch"
        placeholder="Filter tags..."
        class="w-full text-xs px-2.5 py-1 mb-2 bg-gray-50 border-0 rounded-lg focus:outline-none focus:ring-1 focus:ring-[#833dff] box-border"
      />
      <div class="space-y-1 max-h-32 overflow-y-auto overflow-x-hidden w-full">
        <label
          v-for="lab in filteredLabels"
          :key="lab"
          class="flex items-center gap-2 text-xs text-gray-700 hover:bg-gray-50 p-1 rounded cursor-pointer min-w-0"
        >
          <input
            type="checkbox"
            :value="lab"
            :checked="selectedLabels.includes(lab)"
            @change="$emit('toggle-label', lab)"
            class="rounded text-[#833dff] focus:ring-[#833dff] h-3.5 w-3.5 shrink-0"
          />
          <span class="text-xs font-mono truncate min-w-0 flex-1">{{ lab }}</span>
        </label>
      </div>
    </div>

    <!-- Author Filter -->
    <div class="mb-4 w-full min-w-0">
      <label class="block text-xs font-semibold text-gray-700 mb-1">Author</label>
      <select
        :value="resolveAuthor(selectedAuthor, state.activeServer) || selectedAuthor"
        @change="$emit('update-filter', { key: 'author', value: $event.target.value })"
        class="w-full text-xs p-2 rounded-lg bg-gray-50 border-0 focus:outline-none focus:ring-1 focus:ring-[#833dff] max-w-full truncate"
      >
        <option value="">All Authors</option>
        <option v-for="a in displayedAuthors" :key="a" :value="a">{{ a }}</option>
      </select>
    </div>

    <!-- Protocols Search & Autocomplete -->
    <div class="relative w-full min-w-0">
      <div class="flex items-center justify-between mb-1">
        <label class="block text-xs font-semibold text-gray-700">Protocols</label>
        <span v-if="selectedProtocols.length > 0" class="text-[10px] text-purple-700 font-mono font-medium">
          {{ selectedProtocols.length }} active
        </span>
      </div>

      <div class="relative">
        <input
          v-model="protocolInput"
          type="text"
          placeholder="Search protocols..."
          @focus="isProtocolFocused = true"
          @blur="handleProtocolBlur"
          @keydown.enter.prevent="selectTopProtocolSuggestion"
          @keydown.esc="protocolInput = ''; isProtocolFocused = false"
          class="w-full text-xs p-2 rounded-lg bg-gray-50 border-0 focus:outline-none focus:ring-1 focus:ring-[#833dff] text-gray-900 font-mono placeholder:font-sans placeholder:text-gray-400"
        />
        <button
          v-if="protocolInput"
          type="button"
          @click="protocolInput = ''"
          class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs bg-transparent border-0 cursor-pointer p-0 leading-none"
        >
          &times;
        </button>

        <!-- Autocomplete Suggestions Dropdown -->
        <div
          v-if="isProtocolFocused && protocolSuggestions.length > 0"
          class="absolute left-0 right-0 top-full mt-1 bg-white rounded-xl shadow-lg border border-gray-100 z-50 max-h-48 overflow-y-auto py-1"
        >
          <div
            v-for="p in protocolSuggestions"
            :key="p.name"
            @mousedown.prevent="selectProtocolSuggestion(p.name)"
            class="px-2.5 py-1.5 text-xs hover:bg-purple-50 cursor-pointer flex items-center justify-between transition group"
            :class="selectedProtocols.includes(p.name) ? 'bg-purple-50/70 font-semibold text-[#833dff]' : 'text-gray-700'"
          >
            <span class="font-mono text-[11px] truncate flex-1">{{ p.name }}</span>
            <div class="flex items-center gap-1.5 shrink-0 ml-1.5">
              <span class="text-[10px] font-mono text-gray-400 group-hover:text-purple-600">
                {{ p.count }}
              </span>
              <span v-if="selectedProtocols.includes(p.name)" class="text-[10px] text-[#833dff] font-bold">
                ✓
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Selected Protocols Chips -->
      <div v-if="selectedProtocols.length > 0" class="flex flex-wrap gap-1 mt-2">
        <span
          v-for="p in selectedProtocols"
          :key="p"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-purple-100 text-purple-800 font-mono truncate max-w-full"
        >
          <span class="truncate">{{ p }}</span>
          <button
            type="button"
            @click="$emit('toggle-protocol', p)"
            class="hover:text-purple-950 cursor-pointer font-bold leading-none bg-transparent border-0 p-0 text-[11px] shrink-0"
            title="Remove protocol filter"
          >
            &times;
          </button>
        </span>
      </div>
    </div>
  </div>

  <!-- Collapsed Mode Filter Reset Button -->
  <div v-else class="flex flex-col items-center gap-2 w-full">
    <button
      @click="$emit('reset-filters')"
      class="w-9 h-9 flex items-center justify-center transition text-[#833dff] hover:text-purple-800 cursor-pointer bg-transparent hover:bg-transparent border-0 shadow-none"
      :class="isFiltered ? 'opacity-100' : 'opacity-40 pointer-events-none'"
      title="Reset all search filters"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import DateHistogram from '../DateHistogram.vue'
import { state, resolveAuthor } from '../../store.js'

const props = defineProps({
  filterStats: { type: Object, default: () => ({}) },
  fullStats: { type: Object, default: () => ({}) },
  isFiltered: { type: Boolean, default: false },
  selectedAuthor: { type: String, default: '' },
  selectedProtocols: { type: Array, default: () => [] },
  selectedLabels: { type: Array, default: () => [] },
  selectedStartDate: { type: String, default: '' },
  selectedEndDate: { type: String, default: '' },
  selectedDate: { type: String, default: '' },
  isCollapsed: { type: Boolean, default: false }
})

const emit = defineEmits([
  'update-filter',
  'reset-filters',
  'toggle-protocol',
  'toggle-label'
])

const labelSearch = ref('')
const protocolInput = ref('')
const isProtocolFocused = ref(false)

function handleProtocolBlur() {
  setTimeout(() => {
    isProtocolFocused.value = false
  }, 200)
}

const displayedAuthors = computed(() => {
  const baseList = props.fullStats?.authors?.length ? props.fullStats.authors : (props.filterStats?.authors || [])
  const uniqueSet = new Set()
  for (const a of baseList) {
    if (a) {
      uniqueSet.add(resolveAuthor(a, state.activeServer))
    }
  }
  return Array.from(uniqueSet).sort((a, b) => a.localeCompare(b))
})

const displayedLabels = computed(() => {
  return props.fullStats?.labels?.length ? props.fullStats.labels : (props.filterStats?.labels || [])
})

const filteredLabels = computed(() => {
  const all = displayedLabels.value
  if (!labelSearch.value) return all
  return all.filter(l => l.toLowerCase().includes(labelSearch.value.toLowerCase()))
})

const displayedProtocols = computed(() => {
  const baseProtocols = props.fullStats?.protocols?.length ? props.fullStats.protocols : (props.filterStats?.protocols || [])
  if (!props.isFiltered) {
    return baseProtocols
  }
  const filteredMap = new Map((props.filterStats?.protocols || []).map(p => [p.name, p.count]))
  return baseProtocols.map(p => ({
    name: p.name,
    count: filteredMap.get(p.name) || 0,
    fullCount: p.count
  }))
})

const protocolSuggestions = computed(() => {
  const base = displayedProtocols.value
  const q = protocolInput.value.trim().toLowerCase()
  if (!q) {
    return base.slice(0, 8)
  }
  return base
    .filter(p => p.name.toLowerCase().includes(q))
    .slice(0, 10)
})

function selectProtocolSuggestion(name) {
  emit('toggle-protocol', name)
  protocolInput.value = ''
}

function selectTopProtocolSuggestion() {
  if (protocolSuggestions.value.length > 0) {
    selectProtocolSuggestion(protocolSuggestions.value[0].name)
  }
}
</script>
