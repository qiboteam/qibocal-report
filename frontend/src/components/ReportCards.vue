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
          <span class="px-2.5 py-1 rounded-lg text-sm font-bold bg-purple-100 text-purple-800 group-hover:bg-[#833dff] group-hover:text-white transition">
            {{ report.platform }}
          </span>
          <span class="font-mono text-xs font-medium text-gray-700 bg-gray-100 px-2 py-0.5 rounded">
            Q{{ report.targets.join(', Q') }}
          </span>
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
          <div><strong class="text-gray-900">Author:</strong> {{ report.author }}</div>
          <div v-if="(report.tags || report.labels || []).length > 0" class="flex items-center gap-1.5 flex-wrap">
            <strong class="text-gray-900">Tags:</strong>
            <span
              v-for="l in (report.tags || report.labels || [])"
              :key="l"
              class="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 text-purple-700 font-mono"
            >
              {{ l }}
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
          class="px-2 py-0.5 bg-purple-50 hover:bg-purple-100 text-purple-800 rounded-md text-xs font-mono transition"
        >
          {{ proto }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  reports: { type: Array, required: true },
  selected: { type: Array, default: () => [] }
})

defineEmits(['select', 'toggle-select'])
</script>
