<template>
  <aside
    class="no-print h-screen bg-white border-r border-gray-200/80 flex flex-col z-30 shrink-0 relative"
    :class="[
      isCollapsed ? 'w-16' : '',
      isDraggingHorizontal || isDraggingVertical || isDraggingMiddle ? 'select-none transition-none' : 'transition-all duration-100'
    ]"
    :style="!isCollapsed ? { width: `${sidebarWidth}px` } : {}"
  >
    <!-- Top Header: Server Switcher & Collapse Toggle -->
    <sidebar-server-header
      :servers="servers"
      :active-server="activeServer"
      :is-collapsed="isCollapsed"
      @toggle-collapse="isCollapsed = !isCollapsed"
      @select-server="switchServer"
    />

    <!-- Upper Section: Navigation Links -->
    <sidebar-nav-links
      :is-collapsed="isCollapsed"
      :current-report-id="currentReportId"
      :height="topSectionHeight"
    />

    <!-- Draggable Horizontal Splitter between Upper and Lower Sections (Expanded only) -->
    <div
      v-if="!isCollapsed"
      @mousedown="startVerticalResize"
      @dblclick="resetVerticalResize"
      class="h-2 w-full bg-gray-50 hover:bg-purple-100 active:bg-purple-200 cursor-row-resize flex items-center justify-center transition-colors border-y border-gray-200/60 select-none group shrink-0"
      title="Drag to resize sections (double-click to reset)"
    >
      <div class="w-8 h-1 rounded-full bg-gray-300 group-hover:bg-[#833dff] transition-colors"></div>
    </div>
    <div v-else class="w-8 border-b border-gray-200/80 my-1 mx-auto shrink-0"></div>

    <!-- Lower Half: Search Filters / Protocols Summary + Recent History -->
    <div
      class="flex-1 min-h-0 flex flex-col overflow-hidden w-full"
      :class="isCollapsed ? 'items-center' : ''"
    >
      <!-- Section A/B: Search Filters or Protocols Summary -->
      <div
        v-if="isSearchMode || isReportMode"
        class="overflow-y-auto overflow-x-hidden shrink-0 w-full box-border"
        :class="isCollapsed ? 'p-2 flex flex-col items-center flex-1 min-h-0' : 'p-3.5 min-w-0'"
        :style="!isCollapsed && historyOpen ? { height: `${middleSectionHeight}px` } : (!isCollapsed ? { flex: '1 1 0%' } : {})"
      >
        <!-- Search Filters Context -->
        <sidebar-filters
          v-if="isSearchMode"
          :filter-stats="filterStats"
          :full-stats="fullStats"
          :is-filtered="isFiltered"
          :selected-author="selectedAuthor"
          :selected-protocols="selectedProtocols"
          :selected-labels="selectedLabels"
          :selected-count="selectedCount"
          :is-collapsed="isCollapsed"
          @update-filter="$emit('update-filter', $event)"
          @reset-filters="$emit('reset-filters')"
          @toggle-protocol="$emit('toggle-protocol', $event)"
          @toggle-label="$emit('toggle-label', $event)"
          @open-label="$emit('open-label')"
          @open-unlabel="$emit('open-unlabel')"
          @open-author="$emit('open-author')"
          @open-delete="$emit('open-delete')"
          @clear-selection="$emit('clear-selection')"
        />

        <!-- Protocols Summary Context -->
        <sidebar-protocols
          v-else-if="isReportMode"
          :protocols="reportProtocols"
          :report-id="reportId || currentReportId"
          :is-collapsed="isCollapsed"
          :regenerating="regenerating"
          @regenerate="$emit('regenerate')"
          @print-pdf="$emit('print-pdf')"
        />
      </div>

      <!-- Draggable Splitter between Middle Section and Recent History (Expanded only) -->
      <div
        v-if="!isCollapsed && (isSearchMode || isReportMode) && historyOpen"
        @mousedown="startMiddleResize"
        @dblclick="resetMiddleResize"
        class="h-2 w-full bg-gray-50 hover:bg-purple-100 active:bg-purple-200 cursor-row-resize flex items-center justify-center transition-colors border-y border-gray-200/60 select-none group shrink-0"
        title="Drag to resize sections (double-click to reset)"
      >
        <div class="w-8 h-1 rounded-full bg-gray-300 group-hover:bg-[#833dff] transition-colors"></div>
      </div>
      <div v-else-if="isCollapsed && (isSearchMode || isReportMode)" class="w-8 border-b border-gray-200/80 my-1 mx-auto shrink-0"></div>

      <!-- Section C: Recent History -->
      <sidebar-history
        :history="history"
        :is-open="historyOpen"
        :show-top-border="isSearchMode || isReportMode"
        :is-collapsed="isCollapsed"
        @toggle-open="historyOpen = !historyOpen"
      />
    </div>

    <!-- Right Border Resize Handle (horizontal sidebar width, expanded only) -->
    <div
      v-if="!isCollapsed"
      @mousedown="startHorizontalResize"
      @dblclick="resetHorizontalResize"
      class="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-[#833dff]/30 active:bg-[#833dff] transition select-none z-40"
      title="Drag to resize sidebar width (double-click to reset)"
    ></div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { state, setActiveServer } from '../store.js'
import { useResizable } from '../composables/useResize.js'
import SidebarServerHeader from './sidebar/SidebarServerHeader.vue'
import SidebarNavLinks from './sidebar/SidebarNavLinks.vue'
import SidebarFilters from './sidebar/SidebarFilters.vue'
import SidebarProtocols from './sidebar/SidebarProtocols.vue'
import SidebarHistory from './sidebar/SidebarHistory.vue'

defineProps({
  filterStats: { type: Object, default: () => ({}) },
  fullStats: { type: Object, default: () => ({}) },
  isFiltered: { type: Boolean, default: false },
  selectedAuthor: { type: String, default: '' },
  selectedProtocols: { type: Array, default: () => [] },
  selectedLabels: { type: Array, default: () => [] },
  reportProtocols: { type: Array, default: () => [] },
  reportId: { type: String, default: null },
  selectedCount: { type: Number, default: 0 },
  regenerating: { type: Boolean, default: false }
})

defineEmits([
  'update-filter',
  'reset-filters',
  'toggle-protocol',
  'toggle-label',
  'open-label',
  'open-unlabel',
  'open-author',
  'open-delete',
  'clear-selection',
  'regenerate',
  'print-pdf'
])

const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)
const historyOpen = ref(true)

// Horizontal sidebar width resize
const {
  size: sidebarWidth,
  isDragging: isDraggingHorizontal,
  startResize: startHorizontalResize,
  reset: resetHorizontalResize
} = useResizable({
  direction: 'horizontal',
  defaultSize: 288,
  min: 200,
  max: 520,
  storageKey: 'qibocal_sidebar_width',
  disabled: () => isCollapsed.value
})

// Upper section height resize
const {
  size: topSectionHeight,
  isDragging: isDraggingVertical,
  startResize: startVerticalResize,
  reset: resetVerticalResize
} = useResizable({
  direction: 'vertical',
  defaultSize: 180,
  min: 80,
  max: () => window.innerHeight - 180,
  storageKey: 'qibocal_sidebar_top_height',
  disabled: () => isCollapsed.value
})

// Middle section height resize
const {
  size: middleSectionHeight,
  isDragging: isDraggingMiddle,
  startResize: startMiddleResize,
  reset: resetMiddleResize
} = useResizable({
  direction: 'vertical',
  defaultSize: 320,
  min: 80,
  max: () => Math.max(80, window.innerHeight - topSectionHeight.value - 160),
  storageKey: 'qibocal_sidebar_middle_height',
  disabled: () => isCollapsed.value
})

const servers = computed(() => state.servers)
const activeServer = computed(() => state.activeServer)
const history = computed(() => state.history)
const currentReportId = computed(() => state.currentReportId)

const isSearchMode = computed(() => route.path === '/dashboard')
const isReportMode = computed(() => route.path.startsWith('/reports/'))

function switchServer(s) {
  setActiveServer(s)
  if (route.path !== '/dashboard') {
    router.push('/dashboard')
  }
}
</script>
