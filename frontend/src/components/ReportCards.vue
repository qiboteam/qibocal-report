<template>
  <div class="space-y-3.5">
    <div
      v-for="report in reports"
      :key="report.id"
      @click="$emit('select', report)"
      class="bm-card p-5 border border-gray-100 cursor-pointer hover:border-purple-200 transition group"
    >
      <!-- Top header line: Title, platform, date, duration -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-gray-100">
        <div class="flex items-center gap-2.5">
          <h3 class="text-base font-bold text-gray-900 group-hover:text-[#833dff] transition">
            {{ report.title }}
          </h3>
          <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            {{ report.platform }}
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
        <div class="flex items-center gap-4">
          <div><strong class="text-gray-900">Author:</strong> {{ report.author }}</div>
          <div><strong class="text-gray-900">Qubits:</strong> Q{{ report.targets.join(', Q') }}</div>
          <div v-if="report.labels.length > 0" class="flex items-center gap-1">
            <strong class="text-gray-900">Tags:</strong>
            <span v-for="l in report.labels" :key="l" class="text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
              #{{ l }}
            </span>
          </div>
        </div>

        <button
          @click.stop="$emit('select', report)"
          class="bm-btn-primary px-3.5 py-1 text-xs shadow-sm flex items-center gap-1"
        >
          Inspect Report
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
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
  reports: { type: Array, required: true }
})

defineEmits(['select'])
</script>
