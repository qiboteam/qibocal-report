<template>
  <div class="platform-graph-container w-full overflow-x-auto overflow-y-auto p-6 bg-slate-50/60 rounded-2xl border border-gray-200 min-h-[500px]">
    <!-- Graph Header Controls -->
    <div class="flex items-center justify-between gap-4 mb-6 pb-4 border-b border-gray-200/80">
      <div class="flex items-center gap-2">
        <span class="text-xs font-bold uppercase tracking-wider text-gray-400 font-mono">
          Hierarchy Graph
        </span>
        <span class="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 font-mono font-medium">
          {{ totalActiveNodes }} visible nodes
        </span>
      </div>

      <div class="flex items-center gap-3 text-xs text-gray-500">
        <span class="inline-flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded bg-purple-500"></span> Branch
        </span>
        <span class="inline-flex items-center gap-1.5">
          <span class="w-2.5 h-2.5 rounded bg-emerald-500"></span> Scalar / Number List Leaf
        </span>
      </div>
    </div>

    <!-- Multi-Column Tree Graph Layout -->
    <div class="inline-flex items-start gap-8 sm:gap-12 min-w-full pb-4">
      <div
        v-for="(columnNodes, colIdx) in graphColumns"
        :key="colIdx"
        class="flex flex-col gap-4 shrink-0 min-w-[240px] max-w-[340px]"
      >
        <!-- Column Header -->
        <div class="px-2 py-1 bg-gray-200/50 rounded-lg text-[11px] font-mono font-semibold text-gray-600 flex items-center justify-between">
          <span>Depth {{ colIdx }}</span>
          <span class="text-gray-400 font-normal">{{ columnNodes.length }} nodes</span>
        </div>

        <!-- Column Cards -->
        <div class="flex flex-col gap-3">
          <div
            v-for="item in columnNodes"
            :key="item.node.id"
            @click="selectNode(item.node, colIdx)"
            class="graph-node-card p-3 rounded-xl border transition-all duration-150 cursor-pointer relative select-none"
            :class="getNodeClass(item.node, colIdx)"
          >
            <!-- Card Header -->
            <div class="flex items-center justify-between gap-2 mb-1.5">
              <div class="flex items-center gap-1.5 min-w-0">
                <span
                  class="w-2 h-2 rounded-full shrink-0"
                  :class="item.node.isLeaf ? 'bg-emerald-500' : 'bg-[#833dff]'"
                ></span>
                <span class="font-mono text-xs font-bold truncate" :title="item.node.path">
                  {{ item.node.key }}
                </span>
              </div>

              <!-- Badge for branches -->
              <span
                v-if="!item.node.isLeaf"
                class="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold shrink-0"
                :class="selectedPath.startsWith(item.node.path) ? 'bg-purple-200 text-purple-900' : 'bg-gray-100 text-gray-600'"
              >
                {{ (item.node.leafEntries?.length || 0) + (item.node.branchEntries?.length || 0) }}
              </span>
            </div>

            <!-- Card Body: Preview or Leaf Value -->
            <div v-if="item.node.isLeaf" class="mt-1">
              <div
                @click.stop="copyLeaf(item.node)"
                class="px-2 py-1 rounded bg-emerald-50/70 border border-emerald-200/60 hover:border-emerald-300 font-mono text-xs font-semibold text-emerald-900 truncate"
                :title="`Click to copy: ${item.node.value}`"
              >
                {{ formatLeafPreview(item.node.value) }}
              </div>
            </div>

            <div v-else class="mt-1 text-[11px] text-gray-400 font-mono truncate">
              <span v-if="item.node.leafEntries?.length">{{ item.node.leafEntries.length }} leaves</span>
              <span v-if="item.node.leafEntries?.length && item.node.branchEntries?.length"> · </span>
              <span v-if="item.node.branchEntries?.length">{{ item.node.branchEntries.length }} branches</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { formatLeafDisplay } from '../../utils/platformTree.js'
import { copyToClipboard } from '../../utils/clipboard.js'

const props = defineProps({
  rootNode: {
    type: Object,
    required: true
  }
})

// Selected branch path for drilling down column-by-column
const selectedPath = ref('')
const selectedNodesPerDepth = ref([])

function selectNode(node, depth) {
  selectedNodesPerDepth.value = selectedNodesPerDepth.value.slice(0, depth)
  selectedNodesPerDepth.value[depth] = node
  selectedPath.value = node.path
}

const graphColumns = computed(() => {
  const cols = []
  if (!props.rootNode) return cols

  // Column 0: Root's immediate branches and leaves
  const col0 = []
  if (props.rootNode.branchEntries) {
    props.rootNode.branchEntries.forEach(b => col0.push({ node: b, parent: props.rootNode }))
  }
  if (props.rootNode.leafEntries) {
    props.rootNode.leafEntries.forEach(l => col0.push({ node: l, parent: props.rootNode }))
  }
  cols.push(col0)

  // Expand columns for each selected branch
  let currentParent = selectedNodesPerDepth.value[0] || (col0[0] ? col0[0].node : null)

  let depth = 0
  while (currentParent && !currentParent.isLeaf) {
    depth++
    const nextCol = []
    if (currentParent.branchEntries) {
      currentParent.branchEntries.forEach(b => nextCol.push({ node: b, parent: currentParent }))
    }
    if (currentParent.leafEntries) {
      currentParent.leafEntries.forEach(l => nextCol.push({ node: l, parent: currentParent }))
    }

    if (nextCol.length > 0) {
      cols.push(nextCol)
      currentParent = selectedNodesPerDepth.value[depth] || (nextCol[0] ? nextCol[0].node : null)
    } else {
      break
    }
  }

  return cols
})

const totalActiveNodes = computed(() => {
  return graphColumns.value.reduce((acc, col) => acc + col.length, 0)
})

function getNodeClass(node, depth) {
  const isSelected = selectedNodesPerDepth.value[depth]?.id === node.id || selectedPath.value === node.path
  if (isSelected) {
    return 'bg-purple-50/90 border-[#833dff] shadow-sm ring-2 ring-purple-300'
  }
  if (node.isLeaf) {
    return 'bg-white border-gray-200 hover:border-emerald-300 hover:bg-emerald-50/30'
  }
  return 'bg-white border-gray-200 hover:border-purple-300 hover:bg-purple-50/30'
}

function formatLeafPreview(val) {
  const res = formatLeafDisplay(val)
  return res.text
}

function copyLeaf(leafNode) {
  const res = formatLeafDisplay(leafNode.value)
  copyToClipboard(res.raw || res.text)
}
</script>

<style scoped>
.platform-graph-container {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 transparent;
}
.graph-node-card {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
</style>
