<template>
  <div
    class="relative min-w-0 text-left bg-white rounded-xl border border-gray-200 hover:border-purple-400 p-3 shadow-2xs"
  >
    <div class="flex items-center justify-between gap-2">
      <span class="text-xs font-semibold text-gray-800 truncate">{{ index + 1 }}. {{ proto.name }}</span>
      <span class="text-[10px] font-mono" :class="proto.status === 'error' ? 'text-amber-700' : 'text-emerald-700'">{{ proto.status }}</span>
    </div>
    <div class="pointer-events-none" aria-hidden="true">
      <plotly-viewer v-if="proto.figures?.length" :figure="proto.figures[0]" thumbnail />
      <div v-else-if="proto.html" class="h-40 overflow-hidden my-2" inert>
        <div class="thumbnail-table" v-html="proto.html"></div>
      </div>
      <div v-else class="h-40 flex flex-col items-center justify-center gap-2 text-xs text-gray-500">
        <TriangleAlert v-if="proto.error" class="w-8 h-8 text-amber-500" />
        <span>{{ proto.error || 'No figures or tables yet' }}</span>
      </div>
    </div>
    <div class="text-[10px] text-gray-400 font-mono">{{ proto.execution_time || 'N/A' }} · {{ proto.num_figures || proto.figures?.length || 0 }} plots</div>
    <button
      type="button"
      @click="$emit('select')"
      :aria-label="`Open slide ${index + 2}: ${proto.name}`"
      class="absolute inset-0 w-full h-full rounded-xl bg-transparent cursor-pointer focus-visible:outline-purple-500"
    ></button>
  </div>
</template>

<script setup>
import { TriangleAlert } from 'lucide-vue-next'
import PlotlyViewer from '../PlotlyViewer.vue'

defineProps({
  proto: { type: Object, required: true },
  index: { type: Number, required: true }
})
defineEmits(['select'])
</script>

<style scoped>
.thumbnail-table {
  width: 200%;
  transform: scale(0.5);
  transform-origin: top left;
  font-size: 12px;
}

:deep(.thumbnail-table table) {
  width: 100%;
  border-collapse: collapse;
}

:deep(.thumbnail-table th),
:deep(.thumbnail-table td) {
  padding: 8px;
  border-bottom: 1px solid #e5e7eb;
}
</style>
