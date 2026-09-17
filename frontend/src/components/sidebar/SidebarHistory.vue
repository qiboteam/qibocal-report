<template>
  <div v-if="!isCollapsed"
    class="flex flex-col overflow-hidden"
    :class="[
      isOpen ? 'flex-1 min-h-0' : 'shrink-0',
      !isOpen && showTopBorder ? 'border-t border-gray-100' : ''
    ]"
  >
    <div class="p-3.5 pb-2 shrink-0 flex items-center justify-between">
      <button
        @click="$emit('toggle-open')"
        class="w-full flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-800 hover:text-[#833dff] transition cursor-pointer"
      >
        <div class="flex items-center gap-1.5">
          <span>Recent History</span>
          <span v-if="history.length > 0" class="text-[10px] text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded-full font-mono">
            {{ history.length }}
          </span>
        </div>
        <svg
          class="w-3.5 h-3.5 transition text-gray-400"
          :class="isOpen ? 'rotate-180' : ''"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
    </div>

    <div v-if="isOpen" class="flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-3.5 pb-3.5 space-y-1 w-full">
      <div
        v-if="history.length === 0"
        class="py-1 text-[11px] text-gray-400 italic"
      >
        No reports viewed yet
      </div>
      <router-link
        v-for="h in history"
        :key="h.id"
        :to="`/reports/${h.id}`"
        class="block px-2.5 py-1.5 rounded-lg text-xs hover:bg-purple-50/70 border border-transparent hover:border-purple-100 transition truncate"
        :class="$route.params.id === h.id ? 'text-[#833dff] font-semibold bg-purple-50 border-purple-200' : 'text-gray-700'"
        :title="h.id"
      >
        <div class="truncate font-mono font-medium text-[11px]">{{ h.id }}</div>
        <div class="text-[10px] text-gray-400 font-mono flex items-center justify-between mt-0.5">
          <span>{{ h.platform || 'QPU' }}</span>
          <span>{{ h.date }}</span>
        </div>
      </router-link>
    </div>
  </div>

  <!-- Collapsed History Button & Floating Popover -->
  <div v-else class="p-2 relative flex flex-col items-center shrink-0">
    <button
      @click="popoverOpen = !popoverOpen"
      class="w-9 h-9 rounded-xl flex items-center justify-center transition shadow-2xs relative cursor-pointer"
      :class="popoverOpen || history.length > 0
        ? 'bg-purple-50 hover:bg-purple-100 text-[#833dff] border border-purple-200/60'
        : 'bg-gray-50 text-gray-400 border border-gray-200'"
      :title="`Recent History (${history.length} viewed reports)`"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span
        v-if="history.length > 0"
        class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[#833dff] text-white text-[9px] font-bold flex items-center justify-center font-mono shadow-xs"
      >
        {{ history.length > 9 ? '9+' : history.length }}
      </span>
    </button>

    <!-- Floating Popover -->
    <div
      v-if="popoverOpen"
      class="absolute left-full bottom-0 ml-2 w-64 bg-white rounded-2xl shadow-2xl border border-gray-100 p-3 z-50 text-xs"
    >
      <div class="flex items-center justify-between pb-2 border-b border-gray-100 mb-2">
        <div class="font-bold text-gray-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
          <span>Recent History</span>
          <span class="text-[10px] text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded-full font-mono">{{ history.length }}</span>
        </div>
        <button @click="popoverOpen = false" class="text-gray-400 hover:text-gray-600 font-bold text-sm cursor-pointer">&times;</button>
      </div>

      <div class="max-h-60 overflow-y-auto space-y-1">
        <div v-if="history.length === 0" class="py-2 text-[11px] text-gray-400 italic text-center">
          No reports viewed yet
        </div>
        <router-link
          v-for="h in history"
          :key="h.id"
          :to="`/reports/${h.id}`"
          @click="popoverOpen = false"
          class="block px-2.5 py-1.5 rounded-lg text-xs hover:bg-purple-50/70 border border-transparent hover:border-purple-100 transition truncate"
          :class="$route.params.id === h.id ? 'text-[#833dff] font-semibold bg-purple-50 border-purple-200' : 'text-gray-700'"
          :title="h.id"
        >
          <div class="truncate font-mono font-medium text-[11px]">{{ h.id }}</div>
          <div class="text-[10px] text-gray-400 font-mono flex items-center justify-between mt-0.5">
            <span>{{ h.platform || 'QPU' }}</span>
            <span>{{ h.date }}</span>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  history: { type: Array, default: () => [] },
  isOpen: { type: Boolean, default: true },
  showTopBorder: { type: Boolean, default: false },
  isCollapsed: { type: Boolean, default: false }
})

defineEmits(['toggle-open'])
const popoverOpen = ref(false)
</script>
