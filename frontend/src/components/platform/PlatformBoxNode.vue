<template>
  <div
    class="platform-box-node rounded-xl border border-gray-200/90 bg-white transition-all duration-150 overflow-hidden shadow-2xs"
    :class="depthClass"
  >
    <!-- Node Header / Bar -->
    <div
      @click="toggleExpand"
      class="flex items-center justify-between gap-3 px-3.5 py-2.5 bg-gray-50/70 hover:bg-purple-50/50 cursor-pointer select-none transition-colors border-b border-transparent"
      :class="{ '!border-gray-100 bg-gray-50/90': isExpanded }"
    >
      <div class="flex items-center gap-2 min-w-0">
        <!-- Chevron Toggle -->
        <button
          type="button"
          class="w-5 h-5 rounded flex items-center justify-center text-gray-400 hover:text-[#833dff] transition-transform duration-150 shrink-0"
          :class="{ 'rotate-90': isExpanded }"
          tabindex="-1"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" />
          </svg>
        </button>

        <!-- Branch / Folder Icon -->
        <div class="w-6 h-6 rounded-lg flex items-center justify-center shrink-0" :class="iconBgClass">
          <svg v-if="node.depth === 0" class="w-3.5 h-3.5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
          <svg v-else-if="isNumericKey" class="w-3.5 h-3.5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
          </svg>
          <svg v-else class="w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
        </div>

        <!-- Node Key / Title -->
        <span class="font-mono text-xs font-bold text-gray-800 truncate" :title="node.path">
          {{ displayKey }}
        </span>

        <!-- Node Path Sub-label on deeper depths -->
        <span v-if="node.depth > 1" class="text-[10px] text-gray-400 font-mono hidden md:inline truncate">
          {{ node.path }}
        </span>
      </div>

      <!-- Right stats & Copy Path -->
      <div class="flex items-center gap-2 shrink-0">
        <!-- Leaves Count Badge -->
        <span
          v-if="node.leafEntries?.length"
          class="text-[10px] px-2 py-0.5 rounded-full font-mono font-medium bg-purple-50 text-[#833dff] border border-purple-100"
        >
          {{ node.leafEntries.length }} {{ node.leafEntries.length === 1 ? 'val' : 'vals' }}
        </span>

        <!-- Child Branches Count Badge -->
        <span
          v-if="node.branchEntries?.length"
          class="text-[10px] px-2 py-0.5 rounded-full font-mono font-medium bg-gray-100 text-gray-600"
        >
          {{ node.branchEntries.length }} {{ node.branchEntries.length === 1 ? 'node' : 'nodes' }}
        </span>

        <!-- Copy Path Button -->
        <button
          type="button"
          @click.stop="handleCopyPath"
          class="p-1 rounded text-gray-400 hover:text-purple-600 hover:bg-purple-50 transition cursor-pointer"
          :title="`Copy path: ${node.path}`"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Node Content (Expanded) -->
    <div v-show="isExpanded" class="p-3 sm:p-4 space-y-4">
      <!-- Direct Leaf Properties (Grid) -->
      <div v-if="node.leafEntries?.length > 0">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2.5">
          <platform-leaf-property
            v-for="leaf in node.leafEntries"
            :key="leaf.path"
            :leaf="leaf"
          />
        </div>
      </div>

      <!-- Child Branches (Nested Boxes) -->
      <div v-if="node.branchEntries?.length > 0" class="space-y-3 pt-1 border-l-2 border-purple-100 pl-3 sm:pl-4 ml-1 sm:ml-2">
        <platform-box-node
          v-for="branch in node.branchEntries"
          :key="branch.id"
          :node="branch"
          :expand-all="expandAll"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import PlatformLeafProperty from './PlatformLeafProperty.vue'
import { copyToClipboard } from '../../utils/clipboard.js'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  expandAll: {
    type: Boolean,
    default: null
  }
})

// Expand top 2 levels by default
const isExpanded = ref(props.node.depth < 2)

// React to global expandAll/collapseAll changes
watch(() => props.expandAll, (val) => {
  if (val !== null) {
    isExpanded.value = val
  }
})

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}

function handleCopyPath() {
  copyToClipboard(props.node.path)
}

const isNumericKey = computed(() => {
  const k = props.node.key
  return /^\d+$/.test(k) || /^\[\d+\]$/.test(k)
})

const displayKey = computed(() => {
  const k = props.node.key
  if (/^\d+$/.test(k)) {
    return `Qubit ${k}`
  }
  return k
})

const depthClass = computed(() => {
  if (props.node.depth === 0) return 'border-purple-200/80 shadow-xs'
  if (props.node.depth === 1) return 'border-gray-200'
  return 'border-gray-150 bg-gray-50/20'
})

const iconBgClass = computed(() => {
  if (props.node.depth === 0) return 'bg-purple-100'
  if (isNumericKey.value) return 'bg-indigo-100'
  return 'bg-gray-100'
})
</script>

<style scoped>
.platform-box-node {
  transform: translateZ(0);
}
</style>
