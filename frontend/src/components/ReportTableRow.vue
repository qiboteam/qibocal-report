<template>
  <tr
    @click="$emit('select', report)"
    class="hover:bg-purple-50/30 cursor-pointer transition"
    :class="isSelected ? 'bg-purple-50/40' : ''"
  >
    <!-- Checkbox Column -->
    <td class="py-3.5 px-4 w-12 text-center overflow-hidden" @click.stop>
      <input
        type="checkbox"
        :checked="isSelected"
        @change="$emit('toggle-select', report.id)"
        class="rounded text-[#833dff] focus:ring-[#833dff] h-4 w-4 border-gray-300 cursor-pointer"
      />
    </td>

    <!-- Platform Column -->
    <td class="py-3.5 px-4 overflow-hidden">
      <span
        @click.stop="$emit('filter-platform', report.platform)"
        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 hover:bg-purple-200 text-purple-800 hover:text-purple-900 cursor-pointer transition select-none truncate max-w-full"
        :title="`Filter by platform: ${report.platform}`"
      >
        {{ report.platform }}
      </span>
    </td>

    <!-- Qubits Column -->
    <td class="py-3.5 px-4 font-mono text-xs text-gray-600 overflow-hidden">
      <div class="flex flex-wrap gap-1 max-w-full items-center">
        <span
          v-for="t in (report.targets || []).slice(0, 3)"
          :key="String(t)"
          @click.stop="$emit('filter-qubit', String(t))"
          class="px-1.5 py-0.5 rounded text-[11px] font-mono bg-gray-100 hover:bg-purple-100 text-gray-700 hover:text-purple-900 cursor-pointer transition select-none shrink-0"
          :title="`Filter by qubit: Q${t}`"
        >
          Q{{ t }}
        </span>
        <span
          v-if="(report.targets || []).length > 3"
          class="text-[11px] text-gray-400 font-medium px-0.5 shrink-0"
          :title="(report.targets || []).slice(3).map(x => 'Q' + x).join(', ')"
        >
          +{{ report.targets.length - 3 }}
        </span>
        <span
          v-if="!(report.targets && report.targets.length)"
          class="text-gray-300 text-xs"
        >
          —
        </span>
      </div>
    </td>

    <!-- Protocols Column -->
    <td class="py-3.5 px-4 overflow-hidden">
      <div class="flex flex-wrap gap-1 max-w-full">
        <span
          v-for="proto in report.protocols.slice(0, 3)"
          :key="proto"
          @click.stop="$emit('filter-protocol', proto)"
          class="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 hover:bg-purple-100 text-purple-700 hover:text-purple-900 truncate cursor-pointer transition select-none"
          :title="`Filter by protocol: ${proto.replace('_', ' ')}`"
        >
          {{ proto.replace('_', ' ') }}
        </span>
        <span
          v-if="report.protocols.length > 3"
          class="text-[11px] text-gray-400 font-medium px-1 shrink-0"
          :title="report.protocols.slice(3).map(p => p.replace('_', ' ')).join(', ')"
        >
          +{{ report.protocols.length - 3 }}
        </span>
      </div>
    </td>

    <!-- Tags Column -->
    <td class="py-3.5 px-4 overflow-hidden">
      <div class="flex flex-wrap gap-1 max-w-full">
        <span
          v-for="tag in (report.tags || report.labels || []).slice(0, 3)"
          :key="tag"
          @click.stop="$emit('filter-tag', tag)"
          class="group/tag inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 hover:bg-purple-100 text-purple-700 hover:text-purple-900 font-mono truncate cursor-pointer transition select-none"
          :title="`Filter by tag: ${tag}`"
        >
          <span class="truncate">{{ tag }}</span>
          <button
            type="button"
            @click.stop="$emit('remove-tag', { report, tag })"
            class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-red-600 font-bold transition text-[11px] leading-none opacity-60 hover:opacity-100 cursor-pointer shrink-0 ml-0.5"
            title="Remove tag"
          >
            &times;
          </button>
        </span>
        <span
          v-if="(report.tags || report.labels || []).length > 3"
          class="text-[11px] text-gray-400 font-medium px-1 shrink-0"
        >
          +{{ (report.tags || report.labels || []).length - 3 }}
        </span>
        <span
          v-if="!(report.tags || report.labels || []).length"
          class="text-gray-300 text-xs"
        >
          —
        </span>
      </div>
    </td>

    <!-- Author Column -->
    <td class="py-3.5 px-4 text-gray-600 text-xs overflow-hidden">
      <div class="group/author flex items-center gap-1.5 truncate">
        <span
          @click.stop="$emit('filter-author', report.author)"
          class="truncate px-1.5 py-0.5 -ml-1.5 rounded hover:bg-purple-100 text-gray-700 hover:text-purple-900 cursor-pointer transition select-none"
          :title="`Filter by author: ${resolveAuthor(report.author, state.activeServer) || report.author}`"
        >
          {{ resolveAuthor(report.author, state.activeServer) || report.author }}
        </span>
        <button
          @click.stop="$emit('edit-author', report)"
          class="opacity-0 group-hover/author:opacity-100 text-gray-400 hover:text-[#833dff] transition cursor-pointer shrink-0"
          title="Edit author"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>
      </div>
    </td>

    <!-- Date Column -->
    <td class="py-3.5 px-4 text-gray-500 text-xs whitespace-nowrap overflow-hidden">
      <div>{{ report.date }}</div>
      <div class="text-[10px] text-gray-400 font-mono">{{ report.time }}</div>
    </td>
  </tr>
</template>

<script setup>
import { state, resolveAuthor } from '../store.js'

defineProps({
  report: { type: Object, required: true },
  isSelected: { type: Boolean, default: false }
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
