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
    <div class="p-3 border-b border-gray-100 flex items-center justify-between gap-2 shrink-0">
      <div v-if="!isCollapsed" class="flex-1 min-w-0">
        <!-- Quick Switch between registered servers (Issue #3) -->
        <div class="relative">
          <button
            @click="serverDropdownOpen = !serverDropdownOpen"
            class="w-full flex items-center justify-between p-2 rounded-xl bg-gray-50 hover:bg-purple-50 text-left transition border border-gray-100"
          >
            <div class="flex items-center gap-2 truncate">
              <div class="w-6 h-6 rounded-md bg-white p-0.5 shrink-0 shadow-xs" v-html="renderAvatar(activeServer?.avatar || 'quantum-ring')"></div>
              <span class="text-xs font-bold text-gray-800 truncate">{{ activeServer?.name || 'Select Server' }}</span>
            </div>
            <svg class="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Dropdown -->
          <div
            v-if="serverDropdownOpen"
            class="absolute top-full left-0 mt-1 w-full bg-white rounded-xl shadow-xl border border-gray-100 py-1.5 z-50 text-xs"
          >
            <div class="px-3 py-1 font-semibold text-gray-400 uppercase text-[10px]">Registered Servers</div>
            <div
              v-for="s in servers"
              :key="s.id"
              @click="switchServer(s)"
              class="px-3 py-2 hover:bg-purple-50 cursor-pointer flex items-center justify-between gap-2"
              :class="s.id === activeServer?.id ? 'bg-purple-50/60 font-bold text-[#833dff]' : 'text-gray-700'"
            >
              <div class="truncate">
                <div class="truncate">{{ s.name }}</div>
                <div class="text-[10px] font-mono text-gray-400 truncate">{{ s.url }}</div>
              </div>
              <span v-if="s.id === activeServer?.id" class="w-1.5 h-1.5 rounded-full bg-[#833dff] shrink-0"></span>
            </div>
            <div class="border-t border-gray-100 mt-1 pt-1">
              <router-link
                to="/servers"
                @click="serverDropdownOpen = false"
                class="px-3 py-1.5 text-[#833dff] hover:bg-purple-50 flex items-center gap-1.5 font-medium block"
              >
                + Manage Servers...
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- Collapse / Expand Button -->
      <button
        @click="isCollapsed = !isCollapsed"
        class="p-2 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition shrink-0"
        :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path v-if="!isCollapsed" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <!-- UPPER SECTION: Navigation Links -->
    <div
      class="overflow-y-auto p-3 flex flex-col shrink-0 space-y-1"
      :style="!isCollapsed ? { height: `${topSectionHeight}px` } : {}"
    >
      <!-- Search Page -->
      <router-link
        to="/dashboard"
        class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition"
        :class="$route.path === '/dashboard' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100'"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <span v-if="!isCollapsed">Search & Browse</span>
      </router-link>

      <!-- Current Report -->
      <router-link
        v-if="currentReportId"
        :to="`/reports/${currentReportId}`"
        class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition"
        :class="$route.path.startsWith('/reports') ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100'"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <span v-if="!isCollapsed" class="truncate">Current Report</span>
      </router-link>

      <!-- Docs Button -->
      <router-link
        to="/docs"
        class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition"
        :class="$route.path === '/docs' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-700 hover:bg-gray-100'"
      >
        <svg class="w-4 h-4 text-[#833dff] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        <span v-if="!isCollapsed">Documentation</span>
      </router-link>
    </div>

    <!-- Draggable Horizontal Splitter between Upper and Lower Sections -->
    <div
      v-if="!isCollapsed"
      @mousedown="onStartVerticalResize"
      @dblclick="resetVerticalResize"
      class="h-2 w-full bg-gray-50 hover:bg-purple-100 active:bg-purple-200 cursor-row-resize flex items-center justify-center transition-colors border-y border-gray-200/60 select-none group shrink-0"
      title="Drag to resize sections (double-click to reset)"
    >
      <div class="w-8 h-1 rounded-full bg-gray-300 group-hover:bg-[#833dff] transition-colors"></div>
    </div>

    <!-- LOWER HALF: Protocols / Filters + Recent History in Independently Resizable Sections -->
    <div v-if="!isCollapsed" class="flex-1 min-h-0 flex flex-col overflow-hidden w-full">
      <!-- Section A/B: Search Filters or Protocols Summary -->
      <div
        v-if="isSearchMode || isReportMode"
        class="overflow-y-auto overflow-x-hidden p-3.5 shrink-0 w-full min-w-0 box-border"
        :style="historyOpen ? { height: `${middleSectionHeight}px` } : { flex: '1 1 0%' }"
      >
        <!-- Context A: Search Filters -->
        <div v-if="isSearchMode" class="w-full min-w-0">
          <!-- Bulk Selection / Actions (Permanently visible above filters) -->
          <div class="mb-3.5 pb-3 border-b border-gray-100">
            <div class="flex items-center justify-between mb-2">
              <span
                class="text-xs font-medium truncate min-w-0 mr-1"
                :class="selectedCount > 0 ? 'text-purple-900 font-semibold' : 'text-gray-400'"
              >
                {{ selectedCount }} {{ selectedCount === 1 ? 'report' : 'reports' }} selected
              </span>
              <button
                v-if="selectedCount > 0"
                @click="$emit('clear-selection')"
                class="text-[11px] text-gray-400 hover:text-gray-700 underline cursor-pointer shrink-0"
              >
                Deselect
              </button>
            </div>

            <div class="grid grid-cols-2 gap-1.5 w-full">
              <!-- Label Action Button -->
              <button
                @click="selectedCount > 0 && $emit('open-label')"
                :disabled="selectedCount === 0"
                class="px-2 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition min-w-0"
                :class="selectedCount > 0
                  ? 'bg-white border border-purple-200 hover:border-purple-300 hover:bg-purple-50 text-purple-800 shadow-2xs cursor-pointer'
                  : 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'"
                title="Add a label to selected reports"
              >
                <svg
                  class="w-3.5 h-3.5 shrink-0"
                  :class="selectedCount > 0 ? 'text-purple-600' : 'text-gray-400'"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                <span class="truncate">Label</span>
              </button>

              <!-- Unlabel Action Button -->
              <button
                @click="selectedCount > 0 && $emit('open-unlabel')"
                :disabled="selectedCount === 0"
                class="px-2 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition min-w-0"
                :class="selectedCount > 0
                  ? 'bg-white border border-purple-200 hover:border-purple-300 hover:bg-purple-50 text-purple-800 shadow-2xs cursor-pointer'
                  : 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'"
                title="Remove a label from selected reports"
              >
                <svg
                  class="w-3.5 h-3.5 shrink-0"
                  :class="selectedCount > 0 ? 'text-purple-600' : 'text-gray-400'"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
                <span class="truncate">Unlabel</span>
              </button>

              <!-- Author Action Button -->
              <button
                @click="selectedCount > 0 && $emit('open-author')"
                :disabled="selectedCount === 0"
                class="px-2 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition min-w-0"
                :class="selectedCount > 0
                  ? 'bg-white border border-purple-200 hover:border-purple-300 hover:bg-purple-50 text-purple-800 shadow-2xs cursor-pointer'
                  : 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'"
                title="Modify author for selected reports"
              >
                <svg
                  class="w-3.5 h-3.5 shrink-0"
                  :class="selectedCount > 0 ? 'text-purple-600' : 'text-gray-400'"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span class="truncate">Author</span>
              </button>

              <!-- Delete Action Button -->
              <button
                @click="selectedCount > 0 && $emit('open-delete')"
                :disabled="selectedCount === 0"
                class="px-2 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition min-w-0"
                :class="selectedCount > 0
                  ? 'bg-red-600 hover:bg-red-700 text-white shadow-2xs cursor-pointer'
                  : 'bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed'"
                title="Permanently remove selected report folders"
              >
                <svg
                  class="w-3.5 h-3.5 shrink-0"
                  :class="selectedCount > 0 ? 'text-white' : 'text-gray-400'"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <span class="truncate">Delete</span>
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold uppercase tracking-wider text-gray-800">Filters</span>
            <button
              @click="$emit('reset-filters')"
              class="text-[11px] text-[#833dff] hover:underline font-semibold cursor-pointer shrink-0"
            >
              Clear All
            </button>
          </div>

          <!-- Date Range & Histogram (Issue #3) -->
          <div class="mb-4 w-full min-w-0 overflow-hidden">
            <date-histogram
              :histogram="filterStats?.date_histogram"
              @select-date="d => $emit('update-filter', { key: 'date', value: d })"
            />
          </div>

          <!-- Author Filter -->
          <div class="mb-4 w-full min-w-0">
            <label class="block text-xs font-semibold text-gray-700 mb-1">Author</label>
            <select
              :value="selectedAuthor"
              @change="$emit('update-filter', { key: 'author', value: $event.target.value })"
              class="w-full text-xs p-2 rounded-lg bg-gray-50 border border-gray-200 focus:outline-none focus:ring-1 focus:ring-[#833dff] max-w-full truncate"
            >
              <option value="">All Authors</option>
              <option v-for="a in filterStats?.authors" :key="a" :value="a">{{ a }}</option>
            </select>
          </div>

          <!-- Protocols Checklist (sorted by frequency from most to least, Issue #3) -->
          <div class="mb-4 w-full min-w-0">
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-xs font-semibold text-gray-700">Protocols</label>
              <span class="text-[10px] text-gray-400">By frequency</span>
            </div>
            <div class="space-y-1.5 max-h-36 overflow-y-auto overflow-x-hidden pr-1 w-full">
              <label
                v-for="p in filterStats?.protocols"
                :key="p.name"
                class="flex items-center justify-between text-xs text-gray-700 hover:bg-gray-50 p-1 rounded cursor-pointer gap-1.5 min-w-0"
              >
                <div class="flex items-center gap-2 truncate min-w-0 flex-1">
                  <input
                    type="checkbox"
                    :value="p.name"
                    :checked="selectedProtocols.includes(p.name)"
                    @change="$emit('toggle-protocol', p.name)"
                    class="rounded text-[#833dff] focus:ring-[#833dff] h-3.5 w-3.5 shrink-0"
                  />
                  <span class="truncate font-mono text-[11px]">{{ p.name }}</span>
                </div>
                <span class="text-[10px] font-semibold text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded-full shrink-0">
                  {{ p.count }}
                </span>
              </label>
            </div>
          </div>

          <!-- Tags Checklist with Search (Issue #3) -->
          <div class="w-full min-w-0">
            <label class="block text-xs font-semibold text-gray-700 mb-1">Tags</label>
            <input
              v-model="labelSearch"
              placeholder="Filter tags..."
              class="w-full text-xs px-2.5 py-1 mb-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none box-border"
            />
            <div class="space-y-1 max-h-32 overflow-y-auto overflow-x-hidden w-full">
              <label
                v-for="lab in filteredLabels"
                :key="lab"
                class="flex items-center gap-2 text-xs text-gray-700 hover:bg-gray-50 p-1 rounded cursor-pointer min-w-0"
              >
                <input
                  type="checkbox"
                  :value="lab"
                  :checked="selectedLabels.includes(lab)"
                  @change="$emit('toggle-label', lab)"
                  class="rounded text-[#833dff] focus:ring-[#833dff] h-3.5 w-3.5 shrink-0"
                />
                <span class="text-xs font-mono truncate min-w-0 flex-1">{{ lab }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Context B: Protocols Summary on Report View (Issue #3, #10) -->
        <div v-else-if="isReportMode">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold uppercase tracking-wider text-gray-800">Protocols Summary</span>
            <span class="text-[11px] text-purple-700 font-mono bg-purple-100 px-1.5 py-0.5 rounded">
              {{ reportProtocols?.length || 0 }} routines
            </span>
          </div>

          <div class="space-y-1.5">
            <a
              v-for="p in reportProtocols"
              :key="p.id"
              @click.prevent="scrollToProtocol(p.id)"
              class="block p-2 rounded-xl text-xs hover:bg-purple-50/70 border border-gray-100 hover:border-purple-200 transition group cursor-pointer"
            >
              <div class="flex items-center justify-between">
                <span class="font-semibold text-gray-800 group-hover:text-[#833dff] truncate">{{ p.name }}</span>
                <span class="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 rounded">✓</span>
              </div>
              <div class="flex items-center justify-between text-[10px] text-gray-400 mt-1 font-mono">
                <span>{{ p.execution_time || 'N/A' }}</span>
                <span>{{ p.num_figures || (p.figures ? p.figures.length : 0) }} plots</span>
              </div>
            </a>
          </div>
        </div>
      </div>

      <!-- Draggable Horizontal Splitter between Protocols/Filters and Recent History -->
      <div
        v-if="(isSearchMode || isReportMode) && historyOpen"
        @mousedown="onStartMiddleResize"
        @dblclick="resetMiddleResize"
        class="h-2 w-full bg-gray-50 hover:bg-purple-100 active:bg-purple-200 cursor-row-resize flex items-center justify-center transition-colors border-y border-gray-200/60 select-none group shrink-0"
        title="Drag to resize sections (double-click to reset)"
      >
        <div class="w-8 h-1 rounded-full bg-gray-300 group-hover:bg-[#833dff] transition-colors"></div>
      </div>

      <!-- Section C: Recent History (Independently Resizable & Scrollable) -->
      <div
        class="flex flex-col overflow-hidden"
        :class="[
          historyOpen ? 'flex-1 min-h-0' : 'shrink-0',
          !historyOpen && (isSearchMode || isReportMode) ? 'border-t border-gray-100' : ''
        ]"
      >
        <div class="p-3.5 pb-2 shrink-0 flex items-center justify-between">
          <button
            @click="historyOpen = !historyOpen"
            class="w-full flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-800 hover:text-[#833dff] transition cursor-pointer"
          >
            <div class="flex items-center gap-1.5">
              <span>Recent History</span>
              <span v-if="history.length > 0" class="text-[10px] text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded-full font-mono">
                {{ history.length }}
              </span>
            </div>
            <svg class="w-3.5 h-3.5 transition text-gray-400" :class="historyOpen ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        <div v-if="historyOpen" class="flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-3.5 pb-3.5 space-y-1 w-full">
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
    </div>

    <!-- Right Border Resize Handle (for horizontal sidebar width) -->
    <div
      v-if="!isCollapsed"
      @mousedown="onStartHorizontalResize"
      @dblclick="resetHorizontalResize"
      class="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-[#833dff]/30 active:bg-[#833dff] transition select-none z-40"
      title="Drag to resize sidebar width (double-click to reset)"
    ></div>
  </aside>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { state, setActiveServer } from '../store.js'
import { renderAvatar } from './Avatars.js'
import DateHistogram from './DateHistogram.vue'

const props = defineProps({
  filterStats: { type: Object, default: () => ({}) },
  selectedAuthor: { type: String, default: '' },
  selectedProtocols: { type: Array, default: () => [] },
  selectedLabels: { type: Array, default: () => [] },
  reportProtocols: { type: Array, default: () => [] },
  selectedCount: { type: Number, default: 0 }
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
  'clear-selection'
])

const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)
const serverDropdownOpen = ref(false)
const historyOpen = ref(true)
const labelSearch = ref('')

// Sidebar Width Resize State (Horizontal)
const defaultSidebarWidth = 288 // 18rem / w-72
const sidebarWidth = ref(
  parseInt(localStorage.getItem('qibocal_sidebar_width') || String(defaultSidebarWidth), 10)
)
const isDraggingHorizontal = ref(false)

let cleanupHorizontal = null

function onStartHorizontalResize(e) {
  if (isCollapsed.value) return
  isDraggingHorizontal.value = true
  const startX = e.clientX
  const startWidth = sidebarWidth.value

  const onMouseMove = (moveEvent) => {
    if (!isDraggingHorizontal.value) return
    const deltaX = moveEvent.clientX - startX
    const newWidth = Math.max(200, Math.min(520, startWidth + deltaX))
    sidebarWidth.value = newWidth
  }

  const onMouseUp = () => {
    isDraggingHorizontal.value = false
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
    cleanupHorizontal = null
    localStorage.setItem('qibocal_sidebar_width', String(sidebarWidth.value))
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  cleanupHorizontal = onMouseUp
}

function resetHorizontalResize() {
  sidebarWidth.value = defaultSidebarWidth
  localStorage.setItem('qibocal_sidebar_width', String(defaultSidebarWidth))
}

// Sidebar Sections Height Resize State (Vertical Splitter)
const defaultTopHeight = 145 // px
const topSectionHeight = ref(
  parseInt(localStorage.getItem('qibocal_sidebar_top_height') || String(defaultTopHeight), 10)
)
const isDraggingVertical = ref(false)

let cleanupVertical = null

function onStartVerticalResize(e) {
  if (isCollapsed.value) return
  isDraggingVertical.value = true
  const startY = e.clientY
  const startHeight = topSectionHeight.value

  const onMouseMove = (moveEvent) => {
    if (!isDraggingVertical.value) return
    const deltaY = moveEvent.clientY - startY
    const newHeight = Math.max(80, Math.min(window.innerHeight - 180, startHeight + deltaY))
    topSectionHeight.value = newHeight
  }

  const onMouseUp = () => {
    isDraggingVertical.value = false
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
    cleanupVertical = null
    localStorage.setItem('qibocal_sidebar_top_height', String(topSectionHeight.value))
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  cleanupVertical = onMouseUp
}

function resetVerticalResize() {
  topSectionHeight.value = defaultTopHeight
  localStorage.setItem('qibocal_sidebar_top_height', String(defaultTopHeight))
}

// Sidebar Middle Section Height Resize State (Vertical Splitter between Protocols/Filters and History)
const defaultMiddleHeight = 320 // px
const middleSectionHeight = ref(
  parseInt(localStorage.getItem('qibocal_sidebar_middle_height') || String(defaultMiddleHeight), 10)
)
const isDraggingMiddle = ref(false)

let cleanupMiddle = null

function onStartMiddleResize(e) {
  if (isCollapsed.value) return
  isDraggingMiddle.value = true
  const startY = e.clientY
  const startHeight = middleSectionHeight.value

  const onMouseMove = (moveEvent) => {
    if (!isDraggingMiddle.value) return
    const deltaY = moveEvent.clientY - startY
    const minHeight = 80
    const maxHeight = Math.max(minHeight, window.innerHeight - topSectionHeight.value - 160)
    const newHeight = Math.max(minHeight, Math.min(maxHeight, startHeight + deltaY))
    middleSectionHeight.value = newHeight
  }

  const onMouseUp = () => {
    isDraggingMiddle.value = false
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
    cleanupMiddle = null
    localStorage.setItem('qibocal_sidebar_middle_height', String(middleSectionHeight.value))
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  cleanupMiddle = onMouseUp
}

function resetMiddleResize() {
  middleSectionHeight.value = defaultMiddleHeight
  localStorage.setItem('qibocal_sidebar_middle_height', String(defaultMiddleHeight))
}

onUnmounted(() => {
  if (cleanupHorizontal) cleanupHorizontal()
  if (cleanupVertical) cleanupVertical()
  if (cleanupMiddle) cleanupMiddle()
})

const servers = computed(() => state.servers)
const activeServer = computed(() => state.activeServer)
const history = computed(() => state.history)
const currentReportId = computed(() => state.currentReportId)

const isSearchMode = computed(() => route.path === '/dashboard')
const isReportMode = computed(() => route.path.startsWith('/reports/'))

const filteredLabels = computed(() => {
  const all = props.filterStats?.labels || []
  if (!labelSearch.value) return all
  return all.filter(l => l.toLowerCase().includes(labelSearch.value.toLowerCase()))
})

function switchServer(s) {
  setActiveServer(s)
  serverDropdownOpen.value = false
  if (route.path !== '/dashboard') {
    router.push('/dashboard')
  }
}

function scrollToProtocol(id) {
  const el = document.getElementById(`proto-${id}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}
</script>
