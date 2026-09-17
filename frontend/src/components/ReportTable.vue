<template>
  <div class="overflow-x-auto bg-white rounded-xl shadow-sm border border-gray-100">
    <table class="w-full text-left border-collapse text-sm">
      <thead>
        <tr class="bg-gray-50/80 border-b border-gray-100 text-xs text-gray-500 uppercase font-semibold">
          <th class="py-3 px-4 w-10 text-center">
            <input
              type="checkbox"
              :checked="isAllSelected"
              :indeterminate.prop="isIndeterminate"
              @click.stop
              @change="$emit('toggle-select-all')"
              class="rounded text-[#833dff] focus:ring-[#833dff] h-4 w-4 border-gray-300 cursor-pointer"
              title="Select all"
            />
          </th>
          <th class="py-3 px-4">Platform</th>
          <th class="py-3 px-4">Qubits</th>
          <th class="py-3 px-4">Protocols</th>
          <th class="py-3 px-4">Tags</th>
          <th class="py-3 px-4">Author</th>
          <th class="py-3 px-4">Date</th>
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
          <td class="py-3.5 px-4 w-10 text-center" @click.stop>
            <input
              type="checkbox"
              :checked="selected.includes(report.id)"
              @change="$emit('toggle-select', report.id)"
              class="rounded text-[#833dff] focus:ring-[#833dff] h-4 w-4 border-gray-300 cursor-pointer"
            />
          </td>
          <td class="py-3.5 px-4">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">
              {{ report.platform }}
            </span>
          </td>
          <td class="py-3.5 px-4 font-mono text-xs text-gray-600">
            Q{{ report.targets.join(', Q') }}
          </td>
          <td class="py-3.5 px-4">
            <div class="flex flex-wrap gap-1 max-w-sm">
              <span
                v-for="proto in report.protocols.slice(0, 3)"
                :key="proto"
                class="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 text-purple-700"
              >
                {{ proto.replace('_', ' ') }}
              </span>
              <span
                v-if="report.protocols.length > 3"
                class="text-[11px] text-gray-400 font-medium px-1"
              >
                +{{ report.protocols.length - 3 }}
              </span>
            </div>
          </td>
          <td class="py-3.5 px-4">
            <div class="flex flex-wrap gap-1 max-w-xs">
              <span
                v-for="tag in (report.tags || report.labels || []).slice(0, 3)"
                :key="tag"
                class="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 text-purple-700 font-mono"
              >
                {{ tag }}
              </span>
              <span
                v-if="(report.tags || report.labels || []).length > 3"
                class="text-[11px] text-gray-400 font-medium px-1"
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
          <td class="py-3.5 px-4 text-gray-600 text-xs">
            {{ report.author }}
          </td>
          <td class="py-3.5 px-4 text-gray-500 text-xs whitespace-nowrap">
            <div>{{ report.date }}</div>
            <div class="text-[10px] text-gray-400 font-mono">{{ report.time }}</div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

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
</script>
