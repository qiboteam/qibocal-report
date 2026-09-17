<template>
  <div class="overflow-x-auto bg-white rounded-xl shadow-sm border border-gray-100">
    <table
      class="w-full text-left border-collapse text-sm table-fixed"
      :style="{ minWidth: `${totalTableWidth}px` }"
    >
      <colgroup>
        <col
          v-for="col in columns"
          :key="col.key"
          :style="{ width: `${col.width}px` }"
        />
      </colgroup>
      <thead>
        <tr class="bg-gray-50/80 border-b border-gray-100 text-xs text-gray-500 uppercase font-semibold">
          <th
            v-for="(col, index) in columns"
            :key="col.key"
            :style="{ width: `${col.width}px`, minWidth: `${col.minWidth}px` }"
            class="relative py-3 px-4 select-none font-semibold text-xs text-gray-500 uppercase tracking-wider"
            :class="col.key === 'select' ? 'w-12 text-center' : ''"
          >
            <!-- Header Content -->
            <template v-if="col.key === 'select'">
              <input
                type="checkbox"
                :checked="isAllSelected"
                :indeterminate.prop="isIndeterminate"
                @click.stop
                @change="$emit('toggle-select-all')"
                class="rounded text-[#833dff] focus:ring-[#833dff] h-4 w-4 border-gray-300 cursor-pointer"
                title="Select all"
              />
            </template>
            <template v-else>
              <div class="truncate pr-2">{{ col.label }}</div>
            </template>

            <!-- Column Resize Handle -->
            <div
              v-if="col.resizable"
              @mousedown.stop.prevent="startResize(index, $event)"
              @dblclick.stop="resetColumnWidth(index)"
              @click.stop
              class="absolute right-0 top-0 bottom-0 w-3 cursor-col-resize select-none flex justify-center items-center group/resizer z-10"
              :title="`Drag to resize ${col.label} column (double-click to reset)`"
            >
              <div
                class="w-[2px] h-full transition-colors"
                :class="resizingIndex === index ? 'bg-[#833dff]' : 'bg-transparent group-hover/resizer:bg-[#833dff]/70'"
              ></div>
            </div>
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <report-table-row
          v-for="report in reports"
          :key="report.id"
          :report="report"
          :is-selected="selected.includes(report.id)"
          @select="$emit('select', $event)"
          @toggle-select="$emit('toggle-select', $event)"
          @remove-tag="$emit('remove-tag', $event)"
          @edit-author="$emit('edit-author', $event)"
        />
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useTableColumns } from '../composables/useTableColumns.js'
import ReportTableRow from './ReportTableRow.vue'

const props = defineProps({
  reports: { type: Array, required: true },
  selected: { type: Array, default: () => [] }
})

defineEmits(['select', 'toggle-select', 'toggle-select-all', 'remove-tag', 'edit-author'])

const {
  columns,
  totalTableWidth,
  resizingIndex,
  startResize,
  resetColumnWidth
} = useTableColumns()

const isAllSelected = computed(() => {
  return props.reports.length > 0 && props.reports.every(r => props.selected.includes(r.id))
})

const isIndeterminate = computed(() => {
  if (isAllSelected.value) return false
  return props.reports.some(r => props.selected.includes(r.id))
})
</script>
