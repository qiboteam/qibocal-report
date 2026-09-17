<template>
  <div class="w-full min-w-0">
    <!-- Bulk Selection / Actions (Permanently visible above filters) -->
    <div class="mb-3.5 pb-3 border-b border-gray-100">
      <div class="flex items-center justify-between mb-2">
        <span
          class="text-xs font-medium truncate min-w-0 mr-1"
          :class="selectedCount > 0 ? 'text-purple-900 font-semibold' : 'text-gray-400'"
        >
          {{ selectedCount }} {{ selectedCount === 1 ? 'report' : 'reports' }} selected
        </span>
        <button
          v-if="selectedCount > 0"
          @click="$emit('clear-selection')"
          class="text-[11px] text-gray-400 hover:text-gray-700 underline cursor-pointer shrink-0"
        >
          Deselect
        </button>
      </div>

      <div class="grid grid-cols-2 gap-1.5 w-full">
        <!-- Label Action Button -->
        <button
          @click="selectedCount > 0 && $emit('open-label')"
          :disabled="selectedCount === 0"
          class="px-2 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition min-w-0"
          :class="selectedCount > 0
            ? 'bg-white border border-purple-200 hover:border-purple-300 hover:bg-purple-50 text-purple-800 shadow-2xs cursor-pointer'
            : 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'"
          title="Add a label to selected reports"
        >
          <svg
            class="w-3.5 h-3.5 shrink-0"
            :class="selectedCount > 0 ? 'text-purple-600' : 'text-gray-400'"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
          </svg>
          <span class="truncate">Label</span>
        </button>

        <!-- Unlabel Action Button -->
        <button
          @click="selectedCount > 0 && $emit('open-unlabel')"
          :disabled="selectedCount === 0"
          class="px-2 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition min-w-0"
          :class="selectedCount > 0
            ? 'bg-white border border-purple-200 hover:border-purple-300 hover:bg-purple-50 text-purple-800 shadow-2xs cursor-pointer'
            : 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'"
          title="Remove a label from selected reports"
        >
          <svg
            class="w-3.5 h-3.5 shrink-0"
            :class="selectedCount > 0 ? 'text-purple-600' : 'text-gray-400'"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <span class="truncate">Unlabel</span>
        </button>

        <!-- Author Action Button -->
        <button
          @click="selectedCount > 0 && $emit('open-author')"
          :disabled="selectedCount === 0"
          class="px-2 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition min-w-0"
          :class="selectedCount > 0
            ? 'bg-white border border-purple-200 hover:border-purple-300 hover:bg-purple-50 text-purple-800 shadow-2xs cursor-pointer'
            : 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'"
          title="Modify author for selected reports"
        >
          <svg
            class="w-3.5 h-3.5 shrink-0"
            :class="selectedCount > 0 ? 'text-purple-600' : 'text-gray-400'"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span class="truncate">Author</span>
        </button>

        <!-- Delete Action Button -->
        <button
          @click="selectedCount > 0 && $emit('open-delete')"
          :disabled="selectedCount === 0"
          class="px-2 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition min-w-0"
          :class="selectedCount > 0
            ? 'bg-red-600 hover:bg-red-700 text-white shadow-2xs cursor-pointer'
            : 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'"
          title="Permanently remove selected report folders"
        >
          <svg
            class="w-3.5 h-3.5 shrink-0"
            :class="selectedCount > 0 ? 'text-white' : 'text-gray-400'"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          <span class="truncate">Delete</span>
        </button>
      </div>
    </div>

    <!-- Filters Header -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-bold uppercase tracking-wider text-gray-800">Filters</span>
      <button
        @click="$emit('reset-filters')"
        class="text-[11px] text-[#833dff] hover:underline font-semibold cursor-pointer shrink-0"
      >
        Clear All
      </button>
    </div>

    <!-- Date Range & Histogram -->
    <div class="mb-4 w-full min-w-0 overflow-hidden">
      <date-histogram
        :histogram="filterStats?.date_histogram"
        @select-date="d => $emit('update-filter', { key: 'date', value: d })"
      />
    </div>

    <!-- Author Filter -->
    <div class="mb-4 w-full min-w-0">
      <label class="block text-xs font-semibold text-gray-700 mb-1">Author</label>
      <select
        :value="selectedAuthor"
        @change="$emit('update-filter', { key: 'author', value: $event.target.value })"
        class="w-full text-xs p-2 rounded-lg bg-gray-50 border border-gray-200 focus:outline-none focus:ring-1 focus:ring-[#833dff] max-w-full truncate"
      >
        <option value="">All Authors</option>
        <option v-for="a in filterStats?.authors" :key="a" :value="a">{{ a }}</option>
      </select>
    </div>

    <!-- Protocols Checklist (sorted by frequency) -->
    <div class="mb-4 w-full min-w-0">
      <div class="flex items-center justify-between mb-1.5">
        <label class="text-xs font-semibold text-gray-700">Protocols</label>
        <span class="text-[10px] text-gray-400">By frequency</span>
      </div>
      <div class="space-y-1.5 max-h-36 overflow-y-auto overflow-x-hidden pr-1 w-full">
        <label
          v-for="p in filterStats?.protocols"
          :key="p.name"
          class="flex items-center justify-between text-xs text-gray-700 hover:bg-gray-50 p-1 rounded cursor-pointer gap-1.5 min-w-0"
        >
          <div class="flex items-center gap-2 truncate min-w-0 flex-1">
            <input
              type="checkbox"
              :value="p.name"
              :checked="selectedProtocols.includes(p.name)"
              @change="$emit('toggle-protocol', p.name)"
              class="rounded text-[#833dff] focus:ring-[#833dff] h-3.5 w-3.5 shrink-0"
            />
            <span class="truncate font-mono text-[11px]">{{ p.name }}</span>
          </div>
          <span class="text-[10px] font-semibold text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded-full shrink-0">
            {{ p.count }}
          </span>
        </label>
      </div>
    </div>

    <!-- Tags Checklist with Search -->
    <div class="w-full min-w-0">
      <label class="block text-xs font-semibold text-gray-700 mb-1">Tags</label>
      <input
        v-model="labelSearch"
        placeholder="Filter tags..."
        class="w-full text-xs px-2.5 py-1 mb-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none box-border"
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import DateHistogram from '../DateHistogram.vue'

const props = defineProps({
  filterStats: { type: Object, default: () => ({}) },
  selectedAuthor: { type: String, default: '' },
  selectedProtocols: { type: Array, default: () => [] },
  selectedLabels: { type: Array, default: () => [] },
  selectedCount: { type: Number, default: 0 }
})

defineEmits([
  'update-filter',
  'reset-filters',
  'toggle-protocol',
  'toggle-label',
  'open-label',
  'open-unlabel',
  'open-author',
  'open-delete',
  'clear-selection'
])

const labelSearch = ref('')

const filteredLabels = computed(() => {
  const all = props.filterStats?.labels || []
  if (!labelSearch.value) return all
  return all.filter(l => l.toLowerCase().includes(labelSearch.value.toLowerCase()))
})
</script>
