<template>
  <div
    ref="cellRef"
    @click="handleCopy"
    class="leaf-property group flex flex-col justify-between p-2 rounded-lg bg-white border border-gray-100 hover:border-purple-200 hover:shadow-sm transition cursor-pointer select-none relative"
    :title="`Click to copy: ${display.raw || display.text}\nPath: ${leaf.path}`"
  >
    <div class="flex items-center justify-between gap-1.5 mb-1">
      <span class="text-[11px] font-medium text-gray-500 truncate group-hover:text-purple-700 transition-colors">
        {{ leaf.key }}
      </span>
      <span
        v-if="typeBadge"
        class="text-[9px] px-1 py-0.2 rounded font-mono shrink-0 uppercase tracking-wider"
        :class="typeBadgeClass"
      >
        {{ typeBadge }}
      </span>
    </div>

    <div class="flex items-baseline justify-between gap-2 min-w-0">
      <span
        class="font-mono text-xs font-semibold truncate"
        :class="valueColorClass"
      >
        {{ display.text }}
      </span>
      <span
        v-if="display.raw && display.raw !== display.text && display.type === 'number'"
        class="text-[10px] text-gray-400 font-mono truncate shrink-0 hidden sm:inline"
        :title="display.raw"
      >
        {{ display.raw }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatLeafDisplay } from '../../utils/platformTree.js'
import { copyToClipboard } from '../../utils/clipboard.js'

const props = defineProps({
  leaf: {
    type: Object,
    required: true
  }
})

const cellRef = ref(null)
let copyTimer = null

const display = computed(() => {
  return formatLeafDisplay(props.leaf.value)
})

const typeBadge = computed(() => {
  if (display.value.type === 'uncertainty-pair') return 'val ± err'
  if (display.value.type === 'number-list') return 'list'
  if (display.value.type === 'empty-list') return 'empty'
  if (display.value.type === 'boolean') return 'bool'
  if (display.value.type === 'null') return 'null'
  return ''
})

const typeBadgeClass = computed(() => {
  if (display.value.type === 'uncertainty-pair') return 'bg-purple-100 text-purple-700'
  if (display.value.type === 'number-list') return 'bg-blue-100 text-blue-700'
  if (display.value.type === 'empty-list') return 'bg-gray-100 text-gray-500'
  if (display.value.type === 'boolean') return 'bg-emerald-100 text-emerald-700'
  if (display.value.type === 'null') return 'bg-amber-100 text-amber-700'
  return 'bg-gray-100 text-gray-600'
})

const valueColorClass = computed(() => {
  if (display.value.type === 'null') return 'text-gray-400 italic'
  if (display.value.type === 'boolean') return 'text-emerald-700'
  if (display.value.type === 'uncertainty-pair') return 'text-purple-900'
  if (display.value.type === 'number') return 'text-gray-800'
  if (display.value.type === 'string') return 'text-indigo-700 font-sans'
  return 'text-gray-800'
})

function handleCopy() {
  const textToCopy = display.value.raw || display.value.text || String(props.leaf.value)
  copyToClipboard(textToCopy)

  const el = cellRef.value
  if (!el) return

  el.classList.remove('copy-flash')
  void el.offsetWidth
  el.classList.add('copy-flash')

  if (copyTimer) clearTimeout(copyTimer)
  copyTimer = setTimeout(() => {
    el.classList.remove('copy-flash')
    copyTimer = null
  }, 350)
}
</script>

<style scoped>
.leaf-property:hover {
  box-shadow: 0 2px 8px -1px rgba(131, 61, 255, 0.12), 0 1px 3px -1px rgba(0, 0, 0, 0.06);
}

.copy-flash {
  animation: cell-border-flash 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
  position: relative !important;
  z-index: 20 !important;
  outline: 2px solid #833dff !important;
  outline-offset: -2px !important;
}

@keyframes cell-border-flash {
  0% {
    outline: 2px solid #833dff !important;
    outline-offset: -2px !important;
    box-shadow: 0 0 0 3px rgba(131, 61, 255, 0.45), inset 0 0 0 2px #833dff !important;
    border-color: #833dff !important;
    background-color: #f3e8ff !important;
  }
  40% {
    outline: 2px solid #833dff !important;
    outline-offset: -2px !important;
    box-shadow: 0 0 0 2px rgba(131, 61, 255, 0.25), inset 0 0 0 2px #833dff !important;
    border-color: #833dff !important;
    background-color: #f7f1fe !important;
  }
  100% {
    outline: 2px solid transparent !important;
    outline-offset: -2px !important;
    box-shadow: none !important;
    border-color: #f3f4f6 !important;
    background-color: #ffffff !important;
  }
}
</style>
