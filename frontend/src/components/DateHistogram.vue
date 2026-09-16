<template>
  <div v-if="histogram && histogram.length > 0" class="mt-2">
    <div class="flex items-center justify-between text-xs text-gray-500 mb-1.5 font-medium">
      <span>Timeline Distribution</span>
      <span class="text-[10px] text-purple-700 bg-purple-100 px-1.5 py-0.2 rounded font-mono">
        {{ totalCount }} runs
      </span>
    </div>

    <!-- Mini Histogram Bars -->
    <div class="h-12 flex items-end gap-1 bg-gray-50 p-1.5 rounded-lg border border-gray-100">
      <div 
        v-for="bin in histogram" 
        :key="bin.date"
        @click="$emit('select-date', bin.date)"
        :title="`${bin.date}: ${bin.count} reports`"
        class="flex-1 bg-[#c8a8ff] hover:bg-[#833dff] rounded-t transition-all cursor-pointer relative group"
        :style="{ height: `${Math.max(15, (bin.count / maxCount) * 100)}%` }"
      >
        <!-- Floating Tooltip -->
        <div class="opacity-0 group-hover:opacity-100 transition absolute bottom-full left-1/2 -translate-x-1/2 mb-1 pointer-events-none z-30 whitespace-nowrap bg-black text-white text-[10px] px-1.5 py-0.5 rounded shadow">
          {{ bin.date }}: {{ bin.count }}
        </div>
      </div>
    </div>

    <div class="flex justify-between text-[10px] text-gray-400 mt-1 font-mono">
      <span>{{ histogram[0]?.date }}</span>
      <span>{{ histogram[histogram.length - 1]?.date }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  histogram: { type: Array, default: () => [] }
})

defineEmits(['select-date'])

const maxCount = computed(() => {
  if (!props.histogram || props.histogram.length === 0) return 1
  return Math.max(...props.histogram.map(b => b.count), 1)
})

const totalCount = computed(() => {
  if (!props.histogram) return 0
  return props.histogram.reduce((sum, b) => sum + b.count, 0)
})
</script>
