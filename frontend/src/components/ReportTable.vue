<template>
  <div class="overflow-x-auto bg-white rounded-xl shadow-sm border border-gray-100">
    <table
      class="w-full text-left border-collapse text-sm table-fixed"
      :style="{ minWidth: totalTableWidth + 'px' }"
    >
      <colgroup>
        <col
          v-for="col in columns"
          :key="col.key"
          :style="{ width: col.width + 'px' }"
        />
      </colgroup>
      <thead>
        <tr class="bg-gray-50/80 border-b border-gray-100 text-xs text-gray-500 uppercase font-semibold">
          <th
            v-for="(col, index) in columns"
            :key="col.key"
            :style="{ width: col.width + 'px', minWidth: col.minWidth + 'px' }"
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
        <tr
          v-for="report in reports"
          :key="report.id"
          @click="$emit('select', report)"
          class="hover:bg-purple-50/30 cursor-pointer transition"
          :class="selected.includes(report.id) ? 'bg-purple-50/40' : ''"
        >
          <!-- Checkbox Column -->
          <td class="py-3.5 px-4 w-12 text-center overflow-hidden" @click.stop>
            <input
              type="checkbox"
              :checked="selected.includes(report.id)"
              @change="$emit('toggle-select', report.id)"
              class="rounded text-[#833dff] focus:ring-[#833dff] h-4 w-4 border-gray-300 cursor-pointer"
            />
          </td>

          <!-- Platform Column -->
          <td class="py-3.5 px-4 overflow-hidden">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 truncate max-w-full">
              {{ report.platform }}
            </span>
          </td>

          <!-- Qubits Column -->
          <td class="py-3.5 px-4 font-mono text-xs text-gray-600 overflow-hidden">
            <div class="truncate">Q{{ report.targets.join(', Q') }}</div>
          </td>

          <!-- Protocols Column -->
          <td class="py-3.5 px-4 overflow-hidden">
            <div class="flex flex-wrap gap-1 max-w-full">
              <span
                v-for="proto in report.protocols.slice(0, 3)"
                :key="proto"
                class="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 text-purple-700 truncate"
              >
                {{ proto.replace('_', ' ') }}
              </span>
              <span
                v-if="report.protocols.length > 3"
                class="text-[11px] text-gray-400 font-medium px-1 shrink-0"
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
                class="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 text-purple-700 font-mono truncate"
              >
                {{ tag }}
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
            <div class="truncate">{{ report.author }}</div>
          </td>

          <!-- Date Column -->
          <td class="py-3.5 px-4 text-gray-500 text-xs whitespace-nowrap overflow-hidden">
            <div>{{ report.date }}</div>
            <div class="text-[10px] text-gray-400 font-mono">{{ report.time }}</div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'

const props = defineProps({
  reports: { type: Array, required: true },
  selected: { type: Array, default: () => [] }
})

defineEmits(['select', 'toggle-select', 'toggle-select-all'])

const isAllSelected = computed(() => {
  return props.reports.length > 0 && props.reports.every(r => props.selected.includes(r.id))
})

const isIndeterminate = computed(() => {
  if (isAllSelected.value) return false
  return props.reports.some(r => props.selected.includes(r.id))
})

// Columns configuration
const defaultColumns = [
  { key: 'select', label: '', width: 48, minWidth: 48, resizable: false },
  { key: 'platform', label: 'Platform', width: 130, minWidth: 70, resizable: true },
  { key: 'qubits', label: 'Qubits', width: 100, minWidth: 60, resizable: true },
  { key: 'protocols', label: 'Protocols', width: 260, minWidth: 120, resizable: true },
  { key: 'tags', label: 'Tags', width: 190, minWidth: 90, resizable: true },
  { key: 'author', label: 'Author', width: 120, minWidth: 70, resizable: true },
  { key: 'date', label: 'Date', width: 130, minWidth: 80, resizable: true }
]

const STORAGE_KEY = 'qibocal_report_table_columns_v1'

function loadSavedWidths() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      return defaultColumns.map(col => {
        if (parsed[col.key] && typeof parsed[col.key] === 'number') {
          return { ...col, width: Math.max(col.minWidth, parsed[col.key]) }
        }
        return { ...col }
      })
    }
  } catch {
    // Ignore localStorage errors
  }
  return defaultColumns.map(col => ({ ...col }))
}

const columns = ref(loadSavedWidths())

const totalTableWidth = computed(() => {
  return columns.value.reduce((acc, c) => acc + c.width, 0)
})

function saveWidths() {
  try {
    const map = {}
    columns.value.forEach(col => {
      map[col.key] = col.width
    })
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map))
  } catch {
    // Ignore localStorage errors
  }
}

function resetColumnWidth(index) {
  if (defaultColumns[index]) {
    columns.value[index].width = defaultColumns[index].width
    saveWidths()
  }
}

// Resizing logic
const resizingIndex = ref(-1)
let startX = 0
let startWidth = 0

function startResize(index, e) {
  resizingIndex.value = index
  startX = e.clientX
  startWidth = columns.value[index].width

  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'

  window.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('mouseup', handleMouseUp)
}

function handleMouseMove(e) {
  if (resizingIndex.value < 0) return
  const col = columns.value[resizingIndex.value]
  const delta = e.clientX - startX
  col.width = Math.max(col.minWidth, startWidth + delta)
}

function handleMouseUp() {
  if (resizingIndex.value >= 0) {
    saveWidths()
    resizingIndex.value = -1
  }
  document.body.style.cursor = ''
  document.body.style.userSelect = ''

  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mouseup', handleMouseUp)
}

onUnmounted(() => {
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mouseup', handleMouseUp)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
})
</script>
