<template>
  <div v-if="hasData" class="bm-card overflow-hidden border border-gray-100">
    <button
      @click="isOpen = !isOpen"
      class="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50/70 transition cursor-pointer"
    >
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-[#833dff]"></span>
        <h3 class="text-xs font-bold uppercase tracking-wider text-gray-800">
          Hardware Platform Snapshot
        </h3>
      </div>
      <svg
        class="w-4 h-4 text-gray-400 transition"
        :class="isOpen ? 'rotate-180' : ''"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <div v-if="isOpen" class="p-4 border-t border-gray-100 bg-gray-50/50">
      <pre class="p-3 bg-white rounded-xl text-xs font-mono text-gray-700 overflow-x-auto border border-gray-200">{{ JSON.stringify(snapshot, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  snapshot: { type: Object, default: null }
})

const isOpen = ref(false)

const hasData = computed(() => {
  return props.snapshot && typeof props.snapshot === 'object' && Object.keys(props.snapshot).length > 0
})
</script>
