<template>
  <div
    :id="`proto-${proto.id}`"
    class="bm-card p-6 border border-gray-100 page-break"
  >
    <!-- Protocol Header -->
    <div class="flex items-center justify-between pb-3 border-b border-gray-100">
      <div class="flex items-center gap-2.5">
        <span class="w-6 h-6 rounded-lg bg-purple-100 text-[#833dff] font-bold text-xs flex items-center justify-center font-mono">
          {{ index + 1 }}
        </span>
        <h2 class="text-lg font-bold text-gray-900">
          {{ proto.name }}
        </h2>
      </div>

      <div class="flex items-center gap-2">
        <span class="text-xs font-mono text-gray-400">⏱️ {{ proto.execution_time || 'N/A' }}</span>
        <span
          class="px-2 py-0.5 rounded text-xs font-semibold"
          :class="proto.status === 'error' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'"
        >
          {{ proto.status }}
        </span>
      </div>
    </div>

    <!-- Error message if plot could not be generated -->
    <div
      v-if="proto.error"
      class="my-4 p-4 rounded-xl bg-amber-50/80 border border-amber-200/80 text-amber-900 flex items-start gap-3"
    >
      <span class="text-lg leading-none mt-0.5">⚠️</span>
      <div>
        <p class="font-semibold text-xs tracking-wide uppercase text-amber-950">Plot Unavailable</p>
        <p class="text-xs text-amber-800 mt-0.5 leading-relaxed">{{ proto.error }}</p>
      </div>
    </div>

    <!-- Injected Protocol HTML Output -->
    <div v-if="proto.html" class="my-4" v-html="proto.html"></div>

    <!-- Injected Plotly Figures -->
    <div v-if="proto.figures && proto.figures.length > 0" class="mt-4 space-y-4">
      <plotly-viewer
        v-for="fig in proto.figures"
        :key="fig.id || fig.title"
        :figure="fig"
      />
    </div>
    <div v-else-if="!proto.error && !proto.html" class="my-4 text-xs text-gray-400 italic">
      No figures or tables available for this routine.
    </div>
  </div>
</template>

<script setup>
import PlotlyViewer from '../PlotlyViewer.vue'

defineProps({
  proto: { type: Object, required: true },
  index: { type: Number, required: true }
})
</script>
