<template>
  <div v-if="combinedBins && combinedBins.length > 0" :class="[showTitle ? 'mt-2' : '', 'w-full max-w-full overflow-hidden box-border']">
    <!-- Header: Title, Active Range Badge with Clear button, Total runs count -->
    <div v-if="showTitle" class="flex items-center justify-between text-xs text-gray-500 mb-1.5 font-medium gap-1 min-w-0">
      <div class="flex items-center gap-1.5 min-w-0 flex-1">
        <span class="truncate font-semibold text-gray-700">Timeline</span>
        <!-- Active Range Chip with 1-click Clear -->
        <button
          v-if="hasActiveRange"
          type="button"
          @click="clearRange"
          class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-purple-100 text-purple-800 hover:bg-purple-200 transition border-0 cursor-pointer shrink-0 max-w-[140px]"
          title="Clear active time range"
        >
          <span class="truncate">{{ activeRangeText }}</span>
          <span class="font-bold text-purple-600 hover:text-purple-900 leading-none">&times;</span>
        </button>
      </div>

      <!-- Runs count -->
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

    <!-- Histogram Bars Container (Interactive Drag & Click) -->
    <div
      ref="containerRef"
      @pointerdown="handlePointerDown"
      @pointermove="handlePointerMove"
      @pointerup="handlePointerUp"
      @pointercancel="handlePointerCancel"
      :class="[
        heightClass,
        'flex items-end gap-0.5 sm:gap-1 bg-gray-50 p-1.5 rounded-lg border border-gray-100 overflow-hidden w-full relative select-none cursor-crosshair'
      ]"
      title="Click and drag to select a date range, or click a single bar (Shift+click to extend)"
    >
      <div
        v-for="(bin, idx) in combinedBins"
        :key="bin.date"
        :ref="el => { if (el) binElements[idx] = el }"
        class="flex-1 min-w-[2px] h-full flex flex-col justify-end relative group transition-opacity duration-150 rounded-xs"
        :class="isBarDimmed(bin) ? 'opacity-30 grayscale-[50%]' : 'opacity-100'"
        :title="binTooltip(bin)"
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
          :class="[
            barColorClass
              ? barColorClass
              : (isFiltered || isBarInRange(bin))
                ? 'bg-[#833dff] group-hover:bg-[#6c28d9]'
                : 'bg-[#c8a8ff] group-hover:bg-[#833dff]'
          ]"
          :style="{ height: `${Math.max(isFiltered ? 4 : 12, (bin.filteredCount / maxCount) * 100)}%` }"
        ></div>
      </div>

      <!-- Continuous transparent selection rectangle during dragging -->
      <div
        v-if="isDragging && dragBoxStyle"
        class="absolute inset-y-1 rounded-md bg-[#833dff]/15 border border-[#833dff]/40 pointer-events-none z-30"
        :style="dragBoxStyle"
      ></div>
    </div>

    <!-- Date Range Footer Labels -->
    <div
      v-if="combinedBins.length > 0"
      class="flex justify-between text-[10px] text-gray-400 mt-1 font-mono gap-1 overflow-hidden"
    >
      <span class="truncate min-w-0">{{ minAvailableDate }}</span>
      <span class="truncate min-w-0 text-right">{{ maxAvailableDate }}</span>
    </div>

    <!-- Drag Selection Live Preview Notice -->
    <div
      v-if="isDragging && dragRangeText"
      class="text-[10px] font-mono text-[#833dff] bg-purple-50 px-2 py-0.5 rounded mt-1.5 text-center font-semibold border border-purple-200/70 shadow-2xs flex items-center justify-center gap-1.5"
    >
      <span class="w-1.5 h-1.5 rounded-full bg-[#833dff] animate-ping"></span>
      <span>Range: {{ dragRangeText }} ({{ dragRunsCount }} runs)</span>
    </div>

    <!-- Quick Presets and Manual Range Toggle Bar -->
    <div v-if="showPresets" class="flex items-center justify-between mt-1.5 pt-1 text-[11px] gap-1">
      <div class="flex items-center gap-1 shrink-0">
        <button
          type="button"
          v-for="preset in presets"
          :key="preset.id"
          @click="applyPreset(preset)"
          class="px-1.5 py-0.5 rounded text-[10px] font-mono transition border-0 cursor-pointer"
          :class="isPresetActive(preset) ? 'bg-[#833dff] text-white font-semibold' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
          :title="preset.title"
        >
          {{ preset.label }}
        </button>
      </div>

      <button
        type="button"
        @click="showCustomInputs = !showCustomInputs"
        class="text-[10px] text-gray-500 hover:text-[#833dff] font-medium transition cursor-pointer bg-transparent border-0 p-0 flex items-center gap-0.5 shrink-0"
        :class="{ 'text-[#833dff] font-semibold': showCustomInputs || hasActiveRange }"
        title="Toggle exact date inputs"
      >
        <span>{{ showCustomInputs ? 'Close' : 'Pick dates' }}</span>
        <svg
          class="w-3 h-3 transition-transform"
          :class="showCustomInputs ? 'rotate-180' : ''"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
    </div>

    <!-- Collapsible Manual Date Range Inputs -->
    <div
      v-if="showPresets && showCustomInputs"
      class="mt-2 pt-2 border-t border-gray-100 flex items-center gap-1.5 bg-gray-50/70 p-1.5 rounded-lg"
    >
      <div class="flex-1 min-w-0">
        <label class="block text-[9px] uppercase tracking-wider text-gray-500 font-semibold mb-0.5">From</label>
        <input
          type="date"
          :value="effectiveStartDate"
          :min="minAvailableDate"
          :max="maxAvailableDate"
          @change="onManualStartChange"
          class="w-full text-[10px] font-mono px-1.5 py-1 bg-white border border-gray-200 rounded focus:ring-1 focus:ring-[#833dff] focus:outline-none box-border"
        />
      </div>
      <div class="flex-1 min-w-0">
        <label class="block text-[9px] uppercase tracking-wider text-gray-500 font-semibold mb-0.5">To</label>
        <input
          type="date"
          :value="effectiveEndDate"
          :min="minAvailableDate"
          :max="maxAvailableDate"
          @change="onManualEndChange"
          class="w-full text-[10px] font-mono px-1.5 py-1 bg-white border border-gray-200 rounded focus:ring-1 focus:ring-[#833dff] focus:outline-none box-border"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUpdate } from 'vue'

const props = defineProps({
  histogram: { type: Array, default: () => [] },
  fullHistogram: { type: Array, default: () => [] },
  isFiltered: { type: Boolean, default: false },
  startDate: { type: String, default: '' },
  endDate: { type: String, default: '' },
  selectedDate: { type: String, default: '' },
  heightClass: { type: String, default: 'h-14' },
  showTitle: { type: Boolean, default: true },
  showPresets: { type: Boolean, default: true },
  barColorClass: { type: String, default: '' }
})

const emit = defineEmits(['select-date', 'select-range', 'clear-range'])

const containerRef = ref(null)
const binElements = ref([])
const isPointerDown = ref(false)
const isDragging = ref(false)
const dragStartIndex = ref(null)
const dragCurrentIndex = ref(null)
const startPointerX = ref(0)
const startPointerY = ref(0)
const showCustomInputs = ref(false)

onBeforeUpdate(() => {
  binElements.value = []
})

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

const minAvailableDate = computed(() => {
  return combinedBins.value.length > 0 ? combinedBins.value[0].date : ''
})

const maxAvailableDate = computed(() => {
  return combinedBins.value.length > 0 ? combinedBins.value[combinedBins.value.length - 1].date : ''
})

const effectiveStartDate = computed(() => {
  return props.startDate || (props.selectedDate ? props.selectedDate : '')
})

const effectiveEndDate = computed(() => {
  return props.endDate || (props.selectedDate ? props.selectedDate : '')
})

const hasActiveRange = computed(() => {
  return Boolean(effectiveStartDate.value || effectiveEndDate.value)
})

const activeRangeText = computed(() => {
  const s = effectiveStartDate.value
  const e = effectiveEndDate.value
  if (s && e) {
    if (s === e) return s
    return `${s} → ${e}`
  }
  if (s) return `≥ ${s}`
  if (e) return `≤ ${e}`
  return ''
})

const activeSelection = computed(() => {
  if (isDragging.value && dragStartIndex.value !== null && dragCurrentIndex.value !== null) {
    const minIdx = Math.min(dragStartIndex.value, dragCurrentIndex.value)
    const maxIdx = Math.max(dragStartIndex.value, dragCurrentIndex.value)
    return {
      start: combinedBins.value[minIdx]?.date || '',
      end: combinedBins.value[maxIdx]?.date || ''
    }
  }
  if (effectiveStartDate.value || effectiveEndDate.value) {
    return {
      start: effectiveStartDate.value,
      end: effectiveEndDate.value
    }
  }
  return null
})

const dragRangeText = computed(() => {
  if (!isDragging.value || dragStartIndex.value === null || dragCurrentIndex.value === null) return ''
  const minIdx = Math.min(dragStartIndex.value, dragCurrentIndex.value)
  const maxIdx = Math.max(dragStartIndex.value, dragCurrentIndex.value)
  const s = combinedBins.value[minIdx]?.date
  const e = combinedBins.value[maxIdx]?.date
  if (s === e) return s
  return `${s} → ${e}`
})

const dragRunsCount = computed(() => {
  if (!isDragging.value || dragStartIndex.value === null || dragCurrentIndex.value === null) return 0
  const minIdx = Math.min(dragStartIndex.value, dragCurrentIndex.value)
  const maxIdx = Math.max(dragStartIndex.value, dragCurrentIndex.value)
  let count = 0
  for (let i = minIdx; i <= maxIdx; i++) {
    count += combinedBins.value[i]?.fullCount || 0
  }
  return count
})

const dragBoxStyle = computed(() => {
  if (!isDragging.value || dragStartIndex.value === null || dragCurrentIndex.value === null) {
    return null
  }
  const minIdx = Math.min(dragStartIndex.value, dragCurrentIndex.value)
  const maxIdx = Math.max(dragStartIndex.value, dragCurrentIndex.value)

  const startEl = binElements.value[minIdx]
  const endEl = binElements.value[maxIdx]

  if (startEl && endEl) {
    const left = startEl.offsetLeft
    const width = Math.max(2, (endEl.offsetLeft + endEl.offsetWidth) - left)
    return {
      left: `${left}px`,
      width: `${width}px`
    }
  }

  if (containerRef.value && combinedBins.value.length > 0) {
    const rect = containerRef.value.getBoundingClientRect()
    const paddingLeft = 6
    const paddingRight = 6
    const innerWidth = Math.max(1, rect.width - paddingLeft - paddingRight)
    const binWidth = innerWidth / combinedBins.value.length
    const left = paddingLeft + minIdx * binWidth
    const width = Math.max(2, (maxIdx - minIdx + 1) * binWidth)
    return {
      left: `${left}px`,
      width: `${width}px`
    }
  }

  return null
})

function isBarInRange(bin) {
  if (!activeSelection.value) return false
  const { start, end } = activeSelection.value
  if (start && bin.date < start) return false
  if (end && bin.date > end) return false
  return true
}

function isBarDimmed(bin) {
  if (!activeSelection.value) return false
  return !isBarInRange(bin)
}

function binTooltip(bin) {
  const countText = props.isFiltered
    ? `${bin.filteredCount} / ${bin.fullCount} reports`
    : `${bin.fullCount} reports`
  return `${bin.date}: ${countText}\nClick to filter, drag to select range`
}

function getIndexFromEvent(e) {
  if (!containerRef.value || combinedBins.value.length === 0) return 0
  const rect = containerRef.value.getBoundingClientRect()
  const relativeX = e.clientX - rect.left

  // Fast path: find exact bin element under cursor
  if (binElements.value && binElements.value.length === combinedBins.value.length) {
    if (binElements.value[0] && relativeX <= binElements.value[0].offsetLeft) return 0
    const lastEl = binElements.value[binElements.value.length - 1]
    if (lastEl && relativeX >= lastEl.offsetLeft + lastEl.offsetWidth) {
      return binElements.value.length - 1
    }

    for (let i = 0; i < binElements.value.length; i++) {
      const el = binElements.value[i]
      if (el && relativeX >= el.offsetLeft && relativeX <= el.offsetLeft + el.offsetWidth) {
        return i
      }
      if (i < binElements.value.length - 1) {
        const nextEl = binElements.value[i + 1]
        if (nextEl && relativeX > el.offsetLeft + el.offsetWidth && relativeX < nextEl.offsetLeft) {
          const midGap = (el.offsetLeft + el.offsetWidth + nextEl.offsetLeft) / 2
          return relativeX < midGap ? i : i + 1
        }
      }
    }
  }

  // Fallback calculation using container width and percentages
  const paddingLeft = 6
  const paddingRight = 6
  const innerWidth = Math.max(1, rect.width - paddingLeft - paddingRight)
  const clampedX = Math.max(0, Math.min(innerWidth, relativeX - paddingLeft))
  const ratio = clampedX / innerWidth
  const idx = Math.floor(ratio * combinedBins.value.length)
  return Math.min(combinedBins.value.length - 1, Math.max(0, idx))
}

function handlePointerDown(e) {
  if (e.button !== 0) return
  if (combinedBins.value.length === 0) return

  const idx = getIndexFromEvent(e)
  dragStartIndex.value = idx
  dragCurrentIndex.value = idx
  isPointerDown.value = true
  isDragging.value = false
  startPointerX.value = e.clientX
  startPointerY.value = e.clientY

  if (containerRef.value && typeof containerRef.value.setPointerCapture === 'function') {
    try {
      containerRef.value.setPointerCapture(e.pointerId)
    } catch {
      // Ignored
    }
  }
}

function handlePointerMove(e) {
  if (!isPointerDown.value) return
  const dist = Math.hypot(e.clientX - startPointerX.value, e.clientY - startPointerY.value)
  const idx = getIndexFromEvent(e)

  if (!isDragging.value && (dist > 5 || idx !== dragStartIndex.value)) {
    isDragging.value = true
  }

  if (isDragging.value) {
    dragCurrentIndex.value = idx
  }
}

function handlePointerUp(e) {
  if (!isPointerDown.value) return
  isPointerDown.value = false

  if (containerRef.value && typeof containerRef.value.releasePointerCapture === 'function') {
    try {
      if (containerRef.value.hasPointerCapture(e.pointerId)) {
        containerRef.value.releasePointerCapture(e.pointerId)
      }
    } catch {
      // Ignored
    }
  }

  if (isDragging.value && dragStartIndex.value !== null && dragCurrentIndex.value !== null) {
    const minIdx = Math.min(dragStartIndex.value, dragCurrentIndex.value)
    const maxIdx = Math.max(dragStartIndex.value, dragCurrentIndex.value)
    const s = combinedBins.value[minIdx]?.date
    const end = combinedBins.value[maxIdx]?.date
    if (s && end) {
      emit('select-range', { startDate: s, endDate: end })
    }
  } else if (dragStartIndex.value !== null) {
    // Single click
    const clickedDate = combinedBins.value[dragStartIndex.value]?.date
    if (clickedDate) {
      if (e.shiftKey) {
        if (effectiveStartDate.value) {
          const s = effectiveStartDate.value < clickedDate ? effectiveStartDate.value : clickedDate
          const end = (effectiveEndDate.value || effectiveStartDate.value) > clickedDate
            ? (effectiveEndDate.value || effectiveStartDate.value)
            : clickedDate
          emit('select-range', { startDate: s, endDate: end })
        } else {
          emit('select-range', { startDate: clickedDate, endDate: clickedDate })
        }
      } else {
        // If clicking already selected single day, toggle off
        if (effectiveStartDate.value === clickedDate && effectiveEndDate.value === clickedDate) {
          emit('clear-range')
        } else {
          emit('select-range', { startDate: clickedDate, endDate: clickedDate })
          emit('select-date', clickedDate)
        }
      }
    }
  }

  isDragging.value = false
  dragStartIndex.value = null
  dragCurrentIndex.value = null
}

function handlePointerCancel(e) {
  isPointerDown.value = false
  isDragging.value = false
  dragStartIndex.value = null
  dragCurrentIndex.value = null
  if (containerRef.value && typeof containerRef.value.releasePointerCapture === 'function') {
    try {
      if (containerRef.value.hasPointerCapture(e.pointerId)) {
        containerRef.value.releasePointerCapture(e.pointerId)
      }
    } catch {
      // Ignored
    }
  }
}

function clearRange() {
  emit('clear-range')
}

// --- Presets & Manual Inputs ---
const presets = computed(() => [
  { id: 'all', label: 'All', title: 'Show all dates' },
  { id: '7d', label: '7d', title: 'Filter to last 7 days of reports' },
  { id: '30d', label: '30d', title: 'Filter to last 30 days of reports' }
])

function applyPreset(preset) {
  if (preset.id === 'all') {
    emit('clear-range')
    return
  }
  if (combinedBins.value.length === 0) return
  const maxDateStr = combinedBins.value[combinedBins.value.length - 1].date
  const maxDate = new Date(maxDateStr + 'T00:00:00')
  const days = preset.id === '7d' ? 6 : 29
  const startDate = new Date(maxDate)
  startDate.setDate(startDate.getDate() - days)
  const startStr = startDate.toISOString().slice(0, 10)

  emit('select-range', { startDate: startStr, endDate: maxDateStr })
}

function isPresetActive(preset) {
  if (preset.id === 'all') {
    return !hasActiveRange.value
  }
  if (!hasActiveRange.value || combinedBins.value.length === 0) return false
  const maxDateStr = combinedBins.value[combinedBins.value.length - 1].date
  if (effectiveEndDate.value !== maxDateStr) return false
  const maxDate = new Date(maxDateStr + 'T00:00:00')
  const days = preset.id === '7d' ? 6 : 29
  const startDate = new Date(maxDate)
  startDate.setDate(startDate.getDate() - days)
  const startStr = startDate.toISOString().slice(0, 10)
  return effectiveStartDate.value === startStr
}

function onManualStartChange(e) {
  const newStart = e.target.value
  let end = effectiveEndDate.value || maxAvailableDate.value || newStart
  if (newStart && end && newStart > end) {
    end = newStart
  }
  emit('select-range', { startDate: newStart, endDate: end })
}

function onManualEndChange(e) {
  const newEnd = e.target.value
  let start = effectiveStartDate.value || minAvailableDate.value || newEnd
  if (newEnd && start && newEnd < start) {
    start = newEnd
  }
  emit('select-range', { startDate: start, endDate: newEnd })
}
</script>
