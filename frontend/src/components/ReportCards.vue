<template>
  <div class="space-y-3.5">
    <div
      v-for="report in reports"
      :key="report.id"
      @click="$emit('select', report)"
      class="bm-card p-5 border border-gray-100 cursor-pointer hover:border-purple-200 transition group"
      :class="selected.includes(report.id) ? 'border-purple-300 ring-1 ring-purple-300 bg-purple-50/20' : ''"
    >
      <!-- Top header line: checkbox, platform, qubits, date, duration -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-gray-100">
        <div class="flex items-center gap-2.5 flex-wrap">
          <div @click.stop class="flex items-center pr-0.5">
            <input
              type="checkbox"
              :checked="selected.includes(report.id)"
              @change="$emit('toggle-select', report.id)"
              class="rounded text-[#833dff] focus:ring-[#833dff] h-4 w-4 border-gray-300 cursor-pointer"
            />
          </div>
          <span
            @click.stop="$emit('filter-platform', report.platform)"
            class="px-2.5 py-1 rounded-lg text-sm font-bold bg-purple-100 hover:bg-purple-200 text-purple-800 hover:text-purple-900 cursor-pointer transition select-none"
            :title="`Filter by platform: ${report.platform}`"
          >
            {{ report.platform }}
          </span>
          <div v-if="report.targets && report.targets.length > 0" class="flex items-center gap-1">
            <span
              v-for="t in report.targets"
              :key="String(t)"
              @click.stop="$emit('filter-qubit', String(t))"
              class="font-mono text-xs font-medium text-gray-700 bg-gray-100 hover:bg-purple-100 hover:text-purple-900 px-2 py-0.5 rounded cursor-pointer transition select-none"
              :title="`Filter by qubit: Q${t}`"
            >
              Q{{ t }}
            </span>
          </div>
          <span
            v-if="report.has_cached_report"
            class="text-[10px] font-semibold tracking-wider uppercase px-1.5 py-0.5 bg-emerald-100 text-emerald-800 rounded"
            title="Pre-cached report artifacts exist"
          >
            Pre-cached
          </span>
        </div>

        <div class="flex items-center gap-3 text-xs text-gray-500 font-mono">
          <span>📅 {{ report.date }} {{ report.time }}</span>
          <span v-if="report.total_execution_time">⏱️ {{ report.total_execution_time }}</span>
        </div>
      </div>

      <!-- Middle details row -->
      <div class="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-gray-600">
        <div class="flex items-center gap-4 flex-wrap">
          <div class="group/author flex items-center gap-1.5">
            <strong class="text-gray-900">Author:</strong>
            <span
              @click.stop="$emit('filter-author', report.author)"
              class="px-1.5 py-0.5 rounded hover:bg-purple-100 text-gray-700 hover:text-purple-900 cursor-pointer transition select-none"
              :title="`Filter by author: ${resolveAuthor(report.author, state.activeServer) || report.author}`"
            >
              {{ resolveAuthor(report.author, state.activeServer) || report.author }}
            </span>
            <button
              v-if="!isViewer"
              @click.stop="$emit('edit-author', report)"
              class="opacity-0 group-hover/author:opacity-100 text-gray-400 hover:text-[#833dff] transition cursor-pointer"
              title="Edit author"
            >
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
          </div>
          <div v-if="(report.tags || report.labels || []).length > 0" class="flex items-center gap-1.5 flex-wrap">
            <strong class="text-gray-900">Tags:</strong>
            <span
              v-for="l in (report.tags || report.labels || [])"
              :key="l"
              @click.stop="$emit('filter-tag', l)"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 hover:bg-purple-100 text-purple-700 hover:text-purple-900 font-mono cursor-pointer transition select-none"
              :title="`Filter by tag: ${l}`"
            >
              <span>{{ l }}</span>
              <button
                v-if="!isViewer"
                type="button"
                @click.stop="$emit('remove-tag', { report, tag: l })"
                class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-red-600 font-bold transition text-[11px] leading-none opacity-60 hover:opacity-100 cursor-pointer ml-0.5"
                title="Remove tag"
              >
                &times;
              </button>
            </span>
          </div>
        </div>
      </div>

      <!-- Bottom: Protocol chips spanning wide (Inspire style) -->
      <div class="mt-3 pt-2.5 border-t border-gray-50 flex items-center gap-2 flex-wrap">
        <span class="text-xs font-semibold text-gray-500">Protocols:</span>
        <span
          v-for="proto in report.protocols"
          :key="proto"
          @click.stop="$emit('filter-protocol', proto)"
          class="px-2 py-0.5 bg-purple-50 hover:bg-purple-100 text-purple-800 hover:text-purple-900 rounded-md text-xs font-mono transition cursor-pointer select-none"
          :title="`Filter by protocol: ${proto}`"
        >
          {{ proto }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { state, resolveAuthor, isViewer } from '../store.js'

defineProps({
  reports: { type: Array, required: true },
  selected: { type: Array, default: () => [] }
})

defineEmits([
  'select',
  'toggle-select',
  'remove-tag',
  'edit-author',
  'filter-tag',
  'filter-platform',
  'filter-qubit',
  'filter-protocol',
  'filter-author'
])
</script>
