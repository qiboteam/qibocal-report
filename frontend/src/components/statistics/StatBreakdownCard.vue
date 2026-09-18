<template>
  <div class="bm-card p-4 sm:p-5 flex flex-col min-w-0">
    <!-- Header -->
    <div class="flex items-center justify-between pb-3 border-b border-gray-100 mb-3 min-w-0">
      <div class="flex items-center gap-2 min-w-0">
        <div class="w-2.5 h-2.5 rounded-full shrink-0" :class="dotClass"></div>
        <h2 class="text-xs sm:text-sm font-bold text-gray-900 uppercase tracking-wider truncate">
          {{ title }}
        </h2>
      </div>
      <span class="text-xs text-gray-400 font-mono shrink-0">
        {{ items.length }} {{ countLabel }}
      </span>
    </div>

    <!-- Empty State -->
    <div v-if="items.length === 0" class="py-6 text-center text-xs text-gray-400 italic">
      {{ emptyText }}
    </div>

    <!-- Items List -->
    <div v-else class="space-y-2.5 min-w-0">
      <div
        v-for="item in items"
        :key="item.name"
        @click="$emit('select', item.name)"
        class="group p-2.5 rounded-xl transition cursor-pointer border border-transparent min-w-0"
        :class="hoverClass"
        :title="`Filter by ${title.toLowerCase()}: ${item.name}`"
      >
        <div class="flex items-center justify-between mb-1.5 min-w-0 gap-2">
          <!-- Item Name with optional avatar -->
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <slot name="prefix" :item="item"></slot>
            <span
              class="text-xs font-semibold transition truncate min-w-0"
              :class="itemLabelClass"
            >
              {{ item.name || 'Unknown' }}
            </span>
          </div>

          <!-- Count and Percentage -->
          <div class="flex items-center gap-1.5 shrink-0">
            <span class="text-xs font-bold font-mono text-gray-900">{{ item.count }}</span>
            <span class="text-[11px] text-gray-400 font-mono">
              ({{ getPercentage(item.count, total) }}%)
            </span>
            <span class="text-xs opacity-0 group-hover:opacity-100 transition font-semibold" :class="arrowClass">
              &rarr;
            </span>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
          <div
            class="h-1.5 rounded-full transition-all duration-300"
            :class="barGradientClass"
            :style="{ width: `${getPercentage(item.count, total)}%` }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  countLabel: { type: String, default: 'items' },
  items: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
  emptyText: { type: String, default: 'No data found' },
  dotClass: { type: String, default: 'bg-[#833dff]' },
  hoverClass: { type: String, default: 'hover:bg-purple-50/60 hover:border-purple-100' },
  itemLabelClass: { type: String, default: 'font-mono text-gray-800 group-hover:text-[#833dff]' },
  barGradientClass: { type: String, default: 'bg-gradient-to-r from-[#833dff] to-purple-400' },
  arrowClass: { type: String, default: 'text-[#833dff]' }
})

defineEmits(['select'])

function getPercentage(count, total) {
  if (!total || total === 0) return 0
  return Math.min(100, Math.max(0, Math.round((count / total) * 100)))
}
</script>
