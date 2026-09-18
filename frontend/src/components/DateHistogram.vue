<template>
  <div v-if="combinedBins && combinedBins.length > 0" class="mt-2 w-full max-w-full overflow-hidden box-border">
    <div v-if="showTitle" class="flex items-center justify-between text-xs text-gray-500 mb-1.5 font-medium gap-1">
      <span class="truncate">Timeline</span>
      <span
        v-if="isFiltered"
        class="text-[10px] text-purple-700 bg-purple-100 px-1.5 py-0.2 rounded font-mono shrink-0"
        :title="`${totalFilteredCount} filtered out of ${totalFullCount} total runs`"
      >
        {{ totalFilteredCount }} / {{ totalFullCount }} runs
      </span>
      <span
        v-else
        class="text-[10px] text-purple-700 bg-purple-100 px-1.5 py-0.2 rounded font-mono shrink-0"
      >
        {{ totalFullCount }} runs
      </span>
    </div>

    <!-- Histogram Bars Container -->
    <div
      :class="[heightClass, 'flex items-end gap-0.5 sm:gap-1 bg-gray-50 p-1.5 rounded-lg border border-gray-100 overflow-hidden w-full relative']"
    >
      <div
        v-for="bin in combinedBins"
        :key="bin.date"
        @click="$emit('select-date', bin.date)"
        class="flex-1 min-w-[2px] h-full flex flex-col justify-end relative group cursor-pointer"
        :title="isFiltered ? `${bin.date}: ${bin.filteredCount} / ${bin.fullCount} reports` : `${bin.date}: ${bin.fullCount} reports`"
      >
        <!-- Background bar: Full set (greyed out when filtered) -->
        <div
          v-if="isFiltered && bin.fullCount > 0"
          class="w-full bg-gray-200 group-hover:bg-gray-300 rounded-t transition-all absolute bottom-0"
          :style="{ height: `${Math.max(6, (bin.fullCount / maxCount) * 100)}%` }"
        ></div>

        <!-- Foreground bar: Filtered set (accent color) -->
        <div
          v-if="bin.filteredCount > 0"
          class="w-full rounded-t transition-all absolute bottom-0 z-10"
          :class="isFiltered ? 'bg-[#833dff] group-hover:bg-[#6c28d9]' : 'bg-[#c8a8ff] group-hover:bg-[#833dff]'"
          :style="{ height: `${Math.max(isFiltered ? 4 : 12, (bin.filteredCount / maxCount) * 100)}%` }"
        ></div>
      </div>
    </div>

    <!-- Date Range Footer -->
    <div
      v-if="combinedBins.length > 0"
      class="flex justify-between text-[10px] text-gray-400 mt-1 font-mono gap-1 overflow-hidden"
    >
      <span class="truncate min-w-0">{{ combinedBins[0]?.date }}</span>
      <span class="truncate min-w-0 text-right">{{ combinedBins[combinedBins.length - 1]?.date }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  histogram: { type: Array, default: () => [] },
  fullHistogram: { type: Array, default: () => [] },
  isFiltered: { type: Boolean, default: false },
  heightClass: { type: String, default: 'h-12' },
  showTitle: { type: Boolean, default: true }
})

defineEmits(['select-date'])

const combinedBins = computed(() => {
  const full = props.fullHistogram && props.fullHistogram.length > 0 ? props.fullHistogram : []
  const filtered = props.histogram && props.histogram.length > 0 ? props.histogram : []

  const fullMap = new Map(full.map(b => [b.date, b.count]))
  const filteredMap = new Map(filtered.map(b => [b.date, b.count]))

  const dateSet = new Set([...fullMap.keys(), ...filteredMap.keys()])
  const sortedDates = Array.from(dateSet).sort()

  const hasFull = full.length > 0
  const isFiltered = props.isFiltered

  return sortedDates.map(date => {
    const fullCount = hasFull ? (fullMap.get(date) || 0) : (filteredMap.get(date) || 0)
    const filteredCount = isFiltered ? (filteredMap.get(date) || 0) : fullCount

    return {
      date,
      fullCount,
      filteredCount
    }
  })
})

const maxCount = computed(() => {
  if (combinedBins.value.length === 0) return 1
  return Math.max(...combinedBins.value.map(b => Math.max(b.fullCount, b.filteredCount)), 1)
})

const totalFilteredCount = computed(() => {
  return combinedBins.value.reduce((sum, b) => sum + b.filteredCount, 0)
})

const totalFullCount = computed(() => {
  return combinedBins.value.reduce((sum, b) => sum + b.fullCount, 0)
})
</script>
