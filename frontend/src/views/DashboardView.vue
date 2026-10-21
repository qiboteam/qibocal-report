<template>
  <div class="flex h-screen overflow-hidden bg-[#f7f7f7]">
    <!-- Left Sidebar -->
    <sidebar
      :filter-stats="timelineStats"
      :full-stats="filterStats"
      :is-filtered="isTimelineFiltered"
      :selected-author="filters.author"
      :selected-protocols="filters.protocols"
      :selected-labels="filters.labels"
      :selected-start-date="filters.startDate"
      :selected-end-date="filters.endDate"
      :selected-date="filters.date"
      :selected-folder="filters.folder"
      @update-filter="onUpdateFilter"
      @toggle-protocol="onToggleProtocol"
      @toggle-label="onToggleLabel"
      @reset-filters="onResetFilters"
      @open-folder-browser="showFolderBrowser = true"
    />

    <!-- Main Content Panel -->
    <main class="flex-1 flex flex-col min-w-0 overflow-y-auto">
      <!-- Top Bar: Search, View Mode Switcher, Active Server info -->
      <div class="sticky top-0 bg-[#f7f7f7]/90 backdrop-blur-md px-4 sm:px-6 py-3 sm:py-3.5 border-b border-gray-200/70 z-20">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 sm:gap-3 min-w-0">
          <!-- Full-text search input -->
          <div class="relative flex-1 min-w-[160px] max-w-xs">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              ref="searchInput"
              v-model="filters.q"
              type="text"
              placeholder="Search reports..."
              class="w-full pl-9 pr-4 py-2 bg-white rounded-xl text-xs sm:text-sm border-0 focus:outline-none focus:ring-2 focus:ring-[#833dff] shadow-xs"
            />
          </div>

          <!-- Controls: Server Status, Summary Recap, Sort, & View Mode -->
          <div class="flex items-center gap-2 min-w-0 flex-wrap sm:flex-nowrap">
            <!-- Active Server Status Indicator -->
            <div
              class="inline-flex items-center gap-1.5 px-2.5 py-2 rounded-xl text-xs bg-white border border-gray-200 shadow-2xs min-w-0 max-w-xs shrink"
              :title="activeServer?.url ? `${activeServer?.name || 'Server'}: ${activeServer.url}` : (activeServer?.name || 'Local Instance')"
            >
              <span
                class="w-2 h-2 rounded-full shrink-0"
                :class="connectionError ? 'bg-red-500' : loading ? 'bg-amber-400 animate-pulse' : 'bg-emerald-500'"
              ></span>
              <span class="font-semibold text-gray-700 truncate">
                {{ activeServer?.name || 'Local Instance' }}
              </span>
              <span class="text-[10px] font-mono text-gray-400 truncate hidden xl:inline">
                ({{ activeServer?.url || 'local' }})
              </span>
            </div>

            <!--
              The view: one menu for the three ways of looking at the same
              list — the summary, the order, the layout — so the corner holds
              one control instead of three. Closed by a click anywhere else.
            -->
            <div ref="viewMenu" class="relative shrink-0">
              <button
                type="button"
                @click="viewMenuOpen = !viewMenuOpen"
                class="px-2.5 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 shadow-2xs border cursor-pointer"
                :class="viewMenuOpen ? 'bg-[#ebe0ff] text-[#833dff] border-purple-200' : 'bg-white text-gray-600 border-gray-200 hover:text-gray-900'"
                title="Summary, order and layout"
                :aria-expanded="viewMenuOpen"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
                <span>View</span>
                <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              <div
                v-if="viewMenuOpen"
                class="absolute right-0 top-full mt-1.5 w-52 bg-white rounded-xl border border-gray-200 shadow-lg py-1.5 z-30 text-xs"
                role="menu"
              >
                <button
                  type="button"
                  role="menuitemcheckbox"
                  :aria-checked="showRecap"
                  class="w-full flex items-center gap-2 px-3 py-1.5 text-left text-gray-700 hover:bg-purple-50 cursor-pointer"
                  @click="showRecap = !showRecap"
                >
                  <span class="w-3.5 h-3.5 rounded border flex items-center justify-center shrink-0" :class="showRecap ? 'bg-[#833dff] border-[#833dff] text-white' : 'border-gray-300'">
                    <svg v-if="showRecap" class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
                  </span>
                  <span class="flex-1">Statistics summary</span>
                  <span v-if="hasActiveFilters" class="w-1.5 h-1.5 rounded-full bg-[#833dff]" title="Filters apply"></span>
                </button>

                <div class="my-1.5 border-t border-gray-100"></div>
                <div class="px-3 pt-1 pb-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">Order</div>
                <button
                  v-for="option in sortOptions"
                  :key="option.value"
                  type="button"
                  role="menuitemradio"
                  :aria-checked="filters.sort_by === option.value"
                  class="w-full flex items-center gap-2 px-3 py-1.5 text-left hover:bg-purple-50 cursor-pointer"
                  :class="filters.sort_by === option.value ? 'text-[#833dff] font-semibold' : 'text-gray-700'"
                  @click="filters.sort_by = option.value"
                >
                  <span class="w-3.5 h-3.5 flex items-center justify-center shrink-0">
                    <span v-if="filters.sort_by === option.value" class="w-1.5 h-1.5 rounded-full bg-[#833dff]"></span>
                  </span>
                  {{ option.label }}
                </button>

                <div class="my-1.5 border-t border-gray-100"></div>
                <div class="px-3 pt-1 pb-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">Layout</div>
                <button
                  v-for="option in layoutOptions"
                  :key="option.value"
                  type="button"
                  role="menuitemradio"
                  :aria-checked="viewMode === option.value"
                  class="w-full flex items-center gap-2 px-3 py-1.5 text-left hover:bg-purple-50 cursor-pointer"
                  :class="viewMode === option.value ? 'text-[#833dff] font-semibold' : 'text-gray-700'"
                  @click="viewMode = option.value"
                >
                  <span class="w-3.5 h-3.5 flex items-center justify-center shrink-0">
                    <span v-if="viewMode === option.value" class="w-1.5 h-1.5 rounded-full bg-[#833dff]"></span>
                  </span>
                  {{ option.label }}
                </button>
              </div>
            </div>

            <!-- Inside the launcher: what it has to say, as the rightmost element. -->
            <component :is="desktopBell" v-if="desktopBell" toolbar />
          </div>
        </div>

      </div>

      <!-- Main Results Area -->
      <div class="px-4 sm:px-6 pt-4 pb-6">
        <!-- Connection Error Banner -->
        <div
          v-if="connectionError"
          class="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
        >
          <div>
            <div class="font-bold text-xs">Connection Error</div>
            <div class="text-xs mt-0.5 text-red-600">{{ connectionError }}</div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button
              @click="refreshData"
              class="px-3 py-1 bg-white border border-red-200 rounded-lg text-xs font-semibold hover:bg-red-50 transition cursor-pointer"
            >
              Retry
            </button>
            <router-link
              to="/servers"
              class="px-3 py-1 bg-red-600 text-white rounded-lg text-xs font-semibold hover:bg-red-700 transition"
            >
              Manage Servers
            </router-link>
          </div>
        </div>

        <!-- No Server Connected Banner (Static / Fresh client mode) -->
        <div
          v-else-if="!activeServer && (!state.servers || state.servers.length === 0) && !loading"
          class="bg-purple-50 text-purple-900 p-5 rounded-2xl border border-purple-200/80 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-2xs"
        >
          <div>
            <div class="font-bold text-sm">No Report Server Connected</div>
            <div class="text-xs mt-1 text-purple-700">Connect to a local or remote Qibocal report server to explore and analyze calibration runs.</div>
          </div>
          <router-link
            to="/servers"
            class="px-4 py-2 bg-[#833dff] text-white rounded-xl text-xs font-semibold hover:bg-[#722ce6] transition shrink-0 inline-flex items-center gap-1.5 shadow-2xs"
          >
            Connect Server
          </router-link>
        </div>

        <!-- Bulk Success Message Banner -->
        <div
          v-if="bulkSuccessMessage"
          class="mb-4 bg-emerald-50 text-emerald-800 border border-emerald-200 px-4 py-2.5 rounded-xl text-xs flex items-center justify-between gap-2 shadow-2xs animate-fade-in"
        >
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <span class="font-medium">{{ bulkSuccessMessage }}</span>
          </div>
          <button type="button" @click="bulkSuccessMessage = ''" class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-emerald-950 font-bold cursor-pointer leading-none text-base">&times;</button>
        </div>

        <!-- InspireHEP-style Statistics Recap for Filtered Reports -->
        <filtered-recap
          v-if="showRecap && !loading && !connectionError && reports.length > 0"
          :filter-stats="filteredStats || filterStats"
          :full-stats="filterStats"
          :is-filtered="hasActiveFilters"
          :selected-count="selectedReports.length"
          :selected-reports="selectedReportsData"
          :filters="filters"
          :all-filtered-selected="allFilteredSelected"
          :selecting-all="selectingAll"
          @toggle-protocol="onToggleProtocol"
          @filter-platform="onTogglePlatform"
          @filter-author="onToggleAuthor"
          @clear-filter="(key, val) => clearFilter(key, val)"
          @edit-authors-mapping="showAuthorMappingModal = true"
          @select-all-filtered="selectAllFilteredReports"
          @clear-selection="clearSelection"
        />

        <!-- Loading State -->
        <div
          v-if="loading"
          class="bg-white rounded-2xl p-12 text-center border border-gray-200 shadow-sm max-w-lg mx-auto my-8 flex flex-col items-center justify-center animate-fade-in"
        >
          <loading-spinner label="Loading calibration reports..." />
          <p class="text-xs text-gray-500 mt-2">
            Querying <span class="font-medium text-gray-700">{{ activeServer?.name || 'server' }}</span>
            <span v-if="activeServer?.url" class="font-mono text-[11px] text-gray-400"> ({{ activeServer.url }})</span>
          </p>
        </div>

        <!-- Empty State -->
        <div
          v-else-if="reports.length === 0 && !connectionError"
          class="bg-white rounded-2xl p-12 text-center border border-gray-200 shadow-sm max-w-lg mx-auto my-8"
        >
          <div class="w-12 h-12 rounded-xl bg-purple-50 text-[#833dff] flex items-center justify-center mx-auto mb-3">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="font-bold text-base text-gray-900">No calibration reports found</h3>
          <p class="text-xs text-gray-500 mt-1">Try adjusting your filters or point the server to a valid reports folder.</p>
          <button
            @click="onResetFilters"
            class="mt-4 px-4 py-2 rounded-xl text-xs font-semibold bm-btn-secondary"
          >
            Reset All Filters
          </button>
        </div>

        <!-- Table View -->
        <report-table
          v-else-if="viewMode === 'table'"
          :reports="reports"
          :selected="selectedReports"
          :focused-id="focusedId"
          @select="openReport"
          @context-menu="onReportContextMenu"
          @toggle-select="toggleSelect"
          @toggle-select-all="() => toggleSelectAll(reports.map(r => r.id))"
          @remove-tag="payload => removeTagFromReport(payload, fetchStats)"
          @edit-author="r => openAuthorModal(r)"
          @filter-platform="onTogglePlatform"
          @filter-qubit="onToggleQubit"
          @filter-protocol="onToggleProtocol"
          @filter-tag="onToggleLabel"
          @filter-author="onToggleAuthor"
          @preview="openPreviewModal"
        />

        <!-- Horizontal Cards View -->
        <report-cards
          v-else
          :reports="reports"
          :selected="selectedReports"
          :focused-id="focusedId"
          @select="openReport"
          @context-menu="onReportContextMenu"
          @toggle-select="toggleSelect"
          @remove-tag="payload => removeTagFromReport(payload, fetchStats)"
          @edit-author="r => openAuthorModal(r)"
          @filter-platform="onTogglePlatform"
          @filter-qubit="onToggleQubit"
          @filter-protocol="onToggleProtocol"
          @filter-tag="onToggleLabel"
          @filter-author="onToggleAuthor"
          @preview="openPreviewModal"
        />

        <!-- Pagination Controls -->
        <pagination-bar
          v-if="!loading && totalReports > 0"
          :current-page="currentPage"
          :total-pages="totalPages"
          :total-reports="totalReports"
          :page-size="pageSize"
          :pagination-range="paginationRange"
          :visible-pages="visiblePages"
          @change-page="goToPage"
          @update:page-size="onPageSizeChange"
        />
      </div>
    </main>

    <!-- Floating Bulk Actions Bar -->
    <bulk-actions-bar
      :selected-count="selectedReports.length"
      @open-label="openLabelModal"
      @open-unlabel="openUnlabelModal"
      @open-author="() => openAuthorModal()"
      @open-archive="openArchiveModal"
      @open-upload="showUploadModal = true"
      @open-delete="openDeleteModal"
      @clear-selection="clearSelection"
    />

    <!-- Modals -->
    <label-modal
      :show="showLabelModal"
      :selected-count="selectedReports.length"
      :existing-tags="filterStats?.tags || []"
      :loading="bulkActionInProgress"
      :error="bulkError"
      @close="showLabelModal = false"
      @submit="lbl => applyBulkLabel(lbl, onBulkActionSuccess)"
    />

    <unlabel-modal
      :show="showUnlabelModal"
      :selected-count="selectedReports.length"
      :tags-on-selected="tagsOnSelectedReports"
      :loading="bulkActionInProgress"
      :error="bulkError"
      @close="showUnlabelModal = false"
      @submit="lbl => applyBulkUnlabel(lbl, onBulkActionSuccess)"
    />

    <author-modal
      :show="showAuthorModal"
      :is-single-report="Boolean(targetReportIdForAuthor)"
      :selected-count="selectedReports.length"
      :initial-author="authorInitialValue"
      :suggestions="authorSuggestions"
      :loading="bulkActionInProgress"
      :error="bulkError"
      @close="showAuthorModal = false"
      @submit="auth => applyAuthor(auth, onBulkActionSuccess)"
    />

    <delete-confirm-modal
      :show="showDeleteModal"
      :selected-count="selectedReports.length"
      :loading="bulkActionInProgress"
      :error="bulkError"
      @close="showDeleteModal = false"
      @confirm="() => applyBulkDelete(onBulkActionSuccess)"
    />

    <upload-modal
      :show="showUploadModal"
      :report-ids="selectedReports"
      @close="showUploadModal = false"
      @uploaded="onUploaded"
    />

    <archive-modal
      :show="showArchiveModal"
      :selected-count="selectedReports.length"
      :active-filters="activeFiltersForArchive"
      :loading="bulkActionInProgress"
      :error="bulkError"
      @close="showArchiveModal = false"
      @submit="opts => applyBulkArchive({ ...opts, filters: activeFiltersForArchive }, onArchiveSuccess)"
    />

    <author-mapping-modal
      :show="showAuthorMappingModal"
      :server="activeServer"
      @close="showAuthorMappingModal = false"
      @saved="onAuthorMappingSaved"
    />

    <!-- Subfolder Filter Modal -->
    <directory-browser-modal
      :show="showFolderBrowser"
      :server-url="state.activeServer?.url || ''"
      :initial-path="filters.folder"
      :filter-mode="true"
      @close="showFolderBrowser = false"
      @select="handleFolderSelect"
    />

    <!-- Plot Preview Modal -->
    <preview-modal
      :show="showPreviewModal"
      :report="previewReport"
      @close="showPreviewModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { desktopWidget, publishPage } from '../utils/desktop.js'
import { useRouter, useRoute } from 'vue-router'
import { state, addToHistory, apiFetch, ensureServersLoaded, holdReportStats, resolveAuthor, persistSearchState } from '../store.js'
import { REPORT_FIELDS, STATS_FIELDS, apiGraphQL } from '../api.js'
import { openInNewWindow, showContextMenu, wantsNewWindow } from '../utils/newWindow.js'
import { useReportFilters } from '../composables/useReportFilters.js'
import { usePagination } from '../composables/usePagination.js'
import { useBulkActions } from '../composables/useBulkActions.js'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import Sidebar from '../components/Sidebar.vue'
import ReportTable from '../components/ReportTable.vue'
import ReportCards from '../components/ReportCards.vue'
import FilteredRecap from '../components/FilteredRecap.vue'
import { computeStatsFromReports } from '../utils/stats.js'
import PaginationBar from '../components/PaginationBar.vue'
import UploadModal from '../components/modals/UploadModal.vue'
import BulkActionsBar from '../components/BulkActionsBar.vue'
import LabelModal from '../components/modals/LabelModal.vue'
import UnlabelModal from '../components/modals/UnlabelModal.vue'
import AuthorModal from '../components/modals/AuthorModal.vue'
import ArchiveModal from '../components/modals/ArchiveModal.vue'
import DeleteConfirmModal from '../components/modals/DeleteConfirmModal.vue'
import AuthorMappingModal from '../components/modals/AuthorMappingModal.vue'
import DirectoryBrowserModal from '../components/modals/DirectoryBrowserModal.vue'
import PreviewModal from '../components/modals/PreviewModal.vue'

const router = useRouter()
const route = useRoute()
const viewMode = ref('table')
/** The View menu: open or not, and its element, to tell a click inside from one outside. */
const viewMenuOpen = ref(false)
const viewMenu = ref(null)
const sortOptions = [
  { value: 'date_desc', label: 'Newest first' },
  { value: 'date_asc', label: 'Oldest first' }
]
const layoutOptions = [
  { value: 'table', label: 'Table' },
  { value: 'cards', label: 'Cards' }
]
/** The launcher's bell, when this page is inside it. */
const desktopBell = desktopWidget('bell')

function closeViewMenu(event) {
  if (!viewMenuOpen.value) return
  if (event?.type === 'pointerdown' && viewMenu.value?.contains(event.target)) return
  viewMenuOpen.value = false
}
const reports = ref([])

/**
 * The keyboard over the list, as on GitHub: `/` to the search, `j` and
 * `k` along the reports — the one under the cursor is marked — Enter to
 * open it, Escape out of the search or off the list. Nothing fires while
 * typing, or with a modifier held.
 */
const searchInput = ref(null)
const focusedId = ref(null)

function moveFocus(delta) {
  const list = reports.value
  if (!list.length) {
    focusedId.value = null
    return
  }
  const current = list.findIndex(report => report.id === focusedId.value)
  const next = current < 0 ? (delta > 0 ? 0 : list.length - 1) : Math.max(0, Math.min(list.length - 1, current + delta))
  focusedId.value = list[next].id
  requestAnimationFrame(() => document.querySelector('[data-focused="true"]')?.scrollIntoView({ block: 'nearest' }))
}

function onListKeydown(event) {
  if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) return
  const target = event.target
  const typing = target?.closest?.('input, textarea, select, [contenteditable]:not([contenteditable="false"])')
  if (typing) {
    if (event.key === 'Escape' && target === searchInput.value) target.blur()
    return
  }
  if (target?.closest?.('[role="dialog"], .fixed')) return
  switch (event.key) {
    case '/':
      searchInput.value?.focus()
      searchInput.value?.select()
      break
    case 'j': moveFocus(1); break
    case 'k': moveFocus(-1); break
    case 'Enter': {
      const report = reports.value.find(entry => entry.id === focusedId.value)
      if (!report) return
      openReport(report, event)
      break
    }
    case 'Escape':
      if (focusedId.value === null) return
      focusedId.value = null
      break
    default:
      return
  }
  event.preventDefault()
}
const filterStats = ref(null)
const filteredStats = ref(null)
const showRecap = ref(true)
const loading = ref(true)
const connectionError = ref(null)
const showAuthorMappingModal = ref(false)
const showFolderBrowser = ref(false)
const selectingAll = ref(false)
const showPreviewModal = ref(false)
const previewReport = ref(null)

async function onAuthorMappingSaved() {
  await refreshData()
}

const activeServer = computed(() => state.activeServer)

// Composables
const {
  filters,
  hasActiveFilters,
  toggleProtocol,
  toggleLabel,
  togglePlatform,
  toggleAuthor,
  toggleQubit,
  updateFilter,
  resetFilters,
  getFilterQueryKey
} = useReportFilters()

const {
  currentPage,
  pageSize,
  totalReports,
  totalPages,
  paginationRange,
  visiblePages,
  getAccessiblePages,
  getCacheKey,
  clearCache,
  getFromCache,
  setCache,
  hasInCache
} = usePagination(
  state.searchState?.pageSize || 10,
  state.searchState?.currentPage || 1
)

/** The upload dialog, on the reports selected. */
const showUploadModal = ref(false)
function onUploaded({ count, server }) {
  bulkSuccessMessage.value = `${count} report${count === 1 ? '' : 's'} uploaded to ${server.name || server.url}.`
}

const {
  selectedReports,
  bulkActionInProgress,
  bulkError,
  bulkSuccessMessage,
  showLabelModal,
  showUnlabelModal,
  showAuthorModal,
  showArchiveModal,
  showDeleteModal,
  targetReportIdForAuthor,
  authorInitialValue,
  toggleSelect,
  toggleSelectAll,
  clearSelection,
  openLabelModal,
  openUnlabelModal,
  openAuthorModal,
  openArchiveModal,
  openDeleteModal,
  applyBulkLabel,
  applyBulkUnlabel,
  applyAuthor,
  applyBulkDelete,
  applyBulkArchive,
  removeTagFromReport,
  showSuccess
} = useBulkActions()

const activeFiltersForArchive = computed(() => {
  const res = {}
  if (filters.query) res.search = filters.query
  if (filters.folder) res.subfolder = filters.folder
  if (filters.labels?.length) res.tags = [...filters.labels]
  if (filters.protocols?.length) res.protocols = [...filters.protocols]
  if (filters.platform) res.platforms = [filters.platform]
  if (filters.author) res.authors = [filters.author]
  if (filters.qubits?.length) res.qubits = [...filters.qubits]
  return res
})

// Computed metadata
const tagsOnSelectedReports = computed(() => {
  const tags = new Set()
  const sel = selectedReports.value
  for (const r of reports.value) {
    if (sel.includes(r.id)) {
      for (const t of (r.tags || [])) {
        if (t) tags.add(t)
      }
    }
  }
  return Array.from(tags)
})

const selectedReportsData = computed(() => {
  if (selectedReports.value.length === 0) return []
  const idSet = new Set(selectedReports.value)
  return reports.value.filter(r => idSet.has(r.id))
})

const selectedStats = computed(() => {
  if (selectedReportsData.value.length === 0) return null
  return computeStatsFromReports(selectedReportsData.value)
})

const timelineStats = computed(() => {
  if (selectedReports.value.length > 0 && selectedStats.value) {
    return selectedStats.value
  }
  if (hasActiveFilters.value && filteredStats.value) {
    return filteredStats.value
  }
  return filterStats.value
})

const isTimelineFiltered = computed(() => {
  return hasActiveFilters.value || selectedReports.value.length > 0
})

const authorSuggestions = computed(() => {
  const authors = new Set()
  if (activeServer.value?.author_identities) {
    for (const canonical of Object.keys(activeServer.value.author_identities)) {
      authors.add(canonical)
    }
  }
  if (filterStats.value?.authors && Array.isArray(filterStats.value.authors)) {
    for (const a of filterStats.value.authors) {
      if (a && a !== 'Unknown') authors.add(resolveAuthor(a, activeServer.value))
    }
  }
  return Array.from(authors).sort((a, b) => a.localeCompare(b))
})

function getCurrentFilterKey() {
  return getFilterQueryKey(activeServer.value, pageSize.value)
}

/**
 * The neighbouring pages, fetched one at a time once the page is idle —
 * not all at once the moment the current one lands — and only while the
 * filters they were meant for are still the ones on screen.
 */
let prefetchToken = 0
function prefetchAccessiblePages() {
  const token = ++prefetchToken
  const qKey = getCurrentFilterKey()
  const pending = getAccessiblePages(currentPage.value, totalPages.value)
    .filter(p => !hasInCache(getCacheKey(qKey, p)))
  const idle = typeof requestIdleCallback === 'function'
    ? callback => requestIdleCallback(callback, { timeout: 2000 })
    : callback => setTimeout(callback, 300)
  const next = async () => {
    if (token !== prefetchToken || getCurrentFilterKey() !== qKey) return
    const p = pending.shift()
    if (p === undefined) return
    await fetchReports(p, true)
    idle(next)
  }
  idle(next)
}

/** One page over GraphQL, in the shape the REST endpoint answers. */
const PAGE_QUERY = `
  query Page($where: ReportFilter, $page: Int!, $page_size: Int!) {
    reports(where: $where, page: $page, page_size: $page_size) {
      items { ${REPORT_FIELDS} }
      total page page_size total_pages
    }
  }
`
/** The statistics of everything, or of what is filtered. */
const STATS_QUERY = `
  query Stats($where: ReportFilter) {
    stats(where: $where) { ${STATS_FIELDS} }
  }
`

function goToPage(p) {
  if (p < 1 || p > totalPages.value || p === currentPage.value) return
  fetchReports(p, false)
}

async function applyFilterChange(changeFn) {
  if (changeFn) changeFn()
  currentPage.value = 1
  clearCache()
  loading.value = true
  // The new page and its statistics, in one request.
  await loadDashboard(1)
}

function onPageSizeChange(newSize) {
  pageSize.value = newSize
  applyFilterChange()
}

function clearFilter(key, value = null) {
  applyFilterChange(() => {
    if (key === 'author') filters.author = ''
    else if (key === 'platform') filters.platform = ''
    else if (key === 'folder') filters.folder = ''
    else if (key === 'date' || key === 'dateRange') {
      filters.date = ''
      filters.startDate = ''
      filters.endDate = ''
    }
    else if (key === 'protocol') toggleProtocol(value)
    else if (key === 'label') toggleLabel(value)
    else if (key === 'qubit') toggleQubit(value)
    else if (key === 'q') filters.q = ''
  })
}

function handleFolderSelect({ path }) {
  applyFilterChange(() => {
    updateFilter({ key: 'folder', value: path || '' })
  })
}

const allFilteredSelected = computed(() => {
  return totalReports.value > 0 && selectedReports.value.length >= totalReports.value
})

async function selectAllFilteredReports() {
  if (allFilteredSelected.value) {
    clearSelection()
    return
  }
  selectingAll.value = true
  try {
    const params = new URLSearchParams()
    if (filters.q.trim()) params.set('q', filters.q.trim())
    if (filters.sort_by) params.set('sort_by', filters.sort_by)
    if (filters.author) params.set('author', filters.author)
    if (filters.platform) params.set('platform', filters.platform)
    if (filters.folder) params.set('folder', filters.folder)
    const start = filters.startDate || filters.date
    const end = filters.endDate || filters.date
    if (start) params.set('start_date', start)
    if (end) params.set('end_date', end)
    filters.protocols.forEach(p => params.append('protocol', p))
    filters.labels.forEach(l => params.append('tag', l))
    filters.qubits?.forEach(q => params.append('qubit', q))

    const res = await apiFetch(`/api/reports?${params.toString()}`)
    if (res.ok) {
      const data = await res.json()
      const allItems = Array.isArray(data) ? data : (data.items || [])
      selectedReports.value = allItems.map(r => r.id)
    }
  } catch (err) {
    console.error('Failed to select all filtered reports', err)
  } finally {
    selectingAll.value = false
  }
}

function onUpdateFilter(payload) {
  applyFilterChange(() => updateFilter(payload))
}

function onToggleProtocol(p) {
  applyFilterChange(() => toggleProtocol(p))
}

function onToggleLabel(l) {
  applyFilterChange(() => toggleLabel(l))
}

function onTogglePlatform(plat) {
  applyFilterChange(() => togglePlatform(plat))
}

function onToggleAuthor(author) {
  applyFilterChange(() => toggleAuthor(author))
}

function onToggleQubit(qubit) {
  applyFilterChange(() => toggleQubit(qubit))
}

function onResetFilters() {
  applyFilterChange(() => {
    resetFilters()
    clearSelection()
  })
}

/** The address of a report, as a link holds it. */
function reportHref(report, targetProtocol = null) {
  return router.resolve(
    targetProtocol
      ? { path: `/reports/${report.id}`, query: { protocol: targetProtocol } }
      : { path: `/reports/${report.id}` }
  ).href
}

/**
 * The context menu of a row or card inside the application: the webview's
 * own only knows links, and a row is not one. Open here, or in a new window.
 */
function onReportContextMenu(report, event) {
  showContextMenu(event, [
    { text: 'Open', action: () => openReport(report) },
    { text: 'Open in New Window', action: () => openInNewWindow(reportHref(report)) }
  ])
}

/**
 * Open a report: here, or — with a modifier held, the middle button, or
 * Shift+Enter — in a new window, to compare two.
 */
function openReport(report, event = null, targetProtocol = null) {
  if (wantsNewWindow(event)) {
    openInNewWindow(reportHref(report, targetProtocol))
    return
  }
  state.currentReportId = report.id
  addToHistory(report)
  if (targetProtocol) {
    router.push({ path: `/reports/${report.id}`, query: { protocol: targetProtocol } })
  } else {
    router.push(`/reports/${report.id}`)
  }
}

function openPreviewModal(report) {
  previewReport.value = report
  showPreviewModal.value = true
}

function onOpenProtocol({ report, protocol }) {
  openReport(report, null, protocol)
}

async function onBulkActionSuccess() {
  clearCache()
  await Promise.all([fetchStats(), fetchReports(currentPage.value, false)])
  await fetchFilteredStats()
}

async function onArchiveSuccess() {
  clearCache()
  await Promise.all([fetchStats(), fetchReports(currentPage.value, false)])
  await fetchFilteredStats()

  if (currentPage.value > 1 && reports.value.length === 0 && totalReports.value > 0) {
    await fetchReports(1, false)
  }

  // After archiving, if the filtered selection is empty, reset all filters automatically
  if (totalReports.value === 0 && hasActiveFilters.value) {
    onResetFilters()
    showSuccess('Archive created. Filtered selection was empty, all filters reset automatically.')
  }
}

async function refreshData(preservePage = false) {
  const targetPage = preservePage ? (currentPage.value || 1) : 1
  currentPage.value = targetPage
  // Back within the cache's lifetime — a report opened and closed — the same
  // server, filters and page are shown as they were, with no request at all.
  const cached = getFromCache(getCacheKey(getCurrentFilterKey(), targetPage))
  if (cached) {
    reports.value = cached.items
    totalReports.value = cached.total
    totalPages.value = cached.total_pages
    currentPage.value = cached.page
    filterStats.value = cached.stats ?? filterStats.value
    filteredStats.value = cached.filtered ?? (hasActiveFilters.value ? filteredStats.value : filterStats.value)
    loading.value = false
    connectionError.value = null
    if (!filterStats.value) fetchStats().then(fetchFilteredStats)
    prefetchAccessiblePages()
    return
  }
  loading.value = true
  connectionError.value = null
  reports.value = []
  totalReports.value = 0
  filterStats.value = null
  filteredStats.value = null
  clearCache()
  // The page and both statistics, in one request.
  await loadDashboard(targetPage, { everything: true })
}

/**
 * The page, the statistics of everything and the statistics of what is
 * filtered, in one GraphQL request.
 */
const DASHBOARD_QUERY = `
  query Dashboard($where: ReportFilter, $page: Int!, $page_size: Int!, $everything: Boolean!, $filtered: Boolean!) {
    reports(where: $where, page: $page, page_size: $page_size) {
      items { ${REPORT_FIELDS} }
      total page page_size total_pages
    }
    stats @include(if: $everything) { ${STATS_FIELDS} }
    filtered: stats(where: $where) @include(if: $filtered) { ${STATS_FIELDS} }
  }
`

/** The filters as the GraphQL schema takes them: the REST query parameters, named. */
function filterInput() {
  const start = filters.startDate || filters.date
  const end = filters.endDate || filters.date
  return {
    query: filters.q.trim() || null,
    folder: filters.folder || null,
    authors: filters.author ? [filters.author] : null,
    platforms: filters.platform ? [filters.platform] : null,
    protocols: filters.protocols.length ? [...filters.protocols] : null,
    tags: filters.labels.length ? [...filters.labels] : null,
    qubits: filters.qubits?.length ? [...filters.qubits] : null,
    start_date: start || null,
    end_date: end || null,
    sort_by: filters.sort_by || 'date_desc'
  }
}

function showConnectionError(err) {
  if (!activeServer.value && (!state.servers || state.servers.length === 0)) {
    connectionError.value = null
  } else {
    connectionError.value = `Could not connect to ${activeServer.value?.name || 'server'} (${activeServer.value?.url || ''}): ${err.message || 'Network error'}`
  }
  reports.value = []
  loading.value = false
}

async function loadDashboard(page, { everything = false } = {}) {
  if (!activeServer.value && (!state.servers || state.servers.length === 0)) {
    reports.value = []
    totalReports.value = 0
    loading.value = false
    connectionError.value = null
    return
  }
  let data = null
  try {
    data = await apiGraphQL(DASHBOARD_QUERY, {
      where: filterInput(),
      page,
      page_size: pageSize.value,
      everything,
      filtered: hasActiveFilters.value
    })
  } catch (err) {
    console.error('Failed to fetch reports', err)
    showConnectionError(err)
    return
  }
  const pageData = data.reports
  reports.value = pageData.items
  totalReports.value = pageData.total
  totalPages.value = pageData.total_pages
  currentPage.value = pageData.page
  if (everything) {
    filterStats.value = data.stats || filterStats.value
    holdReportStats(filterStats.value)
  }
  filteredStats.value = hasActiveFilters.value ? (data.filtered || filterStats.value) : filterStats.value
  // The statistics travel with the page, so a return shows the whole view at once.
  setCache(getCacheKey(getCurrentFilterKey(), pageData.page), {
    items: pageData.items,
    total: pageData.total,
    total_pages: pageData.total_pages,
    page: pageData.page,
    page_size: pageSize.value,
    stats: filterStats.value,
    filtered: filteredStats.value
  })
  loading.value = false
  connectionError.value = null
  prefetchAccessiblePages()
}

async function fetchStats() {
  try {
    filterStats.value = (await apiGraphQL(STATS_QUERY, { where: null }))?.stats || null
    holdReportStats(filterStats.value)
  } catch (err) {
    console.error('Failed to fetch stats', err)
    filterStats.value = null
  }
}

async function fetchFilteredStats() {
  if (!hasActiveFilters.value) {
    filteredStats.value = filterStats.value
    return
  }
  try {
    filteredStats.value = (await apiGraphQL(STATS_QUERY, { where: filterInput() }))?.stats || null
  } catch (err) {
    console.error('Failed to fetch filtered stats', err)
    filteredStats.value = null
  }
}

async function fetchReports(page = currentPage.value, isPrefetch = false) {
  const qKey = getCurrentFilterKey()
  const cacheKey = getCacheKey(qKey, page)

  if (hasInCache(cacheKey)) {
    if (!isPrefetch) {
      const cached = getFromCache(cacheKey)
      reports.value = cached.items
      totalReports.value = cached.total
      totalPages.value = cached.total_pages
      currentPage.value = cached.page
      loading.value = false
      connectionError.value = null
      prefetchAccessiblePages()
    }
    return
  }

  if (!isPrefetch) {
    if (!activeServer.value && (!state.servers || state.servers.length === 0)) {
      reports.value = []
      totalReports.value = 0
      loading.value = false
      connectionError.value = null
      return
    }
    loading.value = true
    connectionError.value = null
  }

  try {
    const data = (await apiGraphQL(PAGE_QUERY, { where: filterInput(), page, page_size: pageSize.value })).reports
    setCache(cacheKey, {
      items: data.items,
      total: data.total,
      total_pages: data.total_pages,
      page: data.page,
      page_size: pageSize.value,
      stats: filterStats.value,
      filtered: filteredStats.value
    })
    if (!isPrefetch) {
      reports.value = data.items
      totalReports.value = data.total
      totalPages.value = data.total_pages
      currentPage.value = data.page
      loading.value = false
      prefetchAccessiblePages()
    }
  } catch (err) {
    if (!isPrefetch) {
      console.error('Failed to fetch reports', err)
      showConnectionError(err)
    }
  }
}

// Watchers and lifecycle
function syncFiltersFromRoute(query) {
  let changed = false
  if (query.label) {
    const lbl = String(query.label)
    if (!filters.labels.includes(lbl)) {
      filters.labels = [lbl]
      changed = true
    }
  }
  if (query.platform) {
    const plat = String(query.platform)
    if (filters.platform !== plat) {
      filters.platform = plat
      changed = true
    }
  }
  if (query.protocol) {
    const proto = String(query.protocol)
    if (!filters.protocols.includes(proto)) {
      filters.protocols = [proto]
      changed = true
    }
  }
  if (query.author) {
    const aut = String(query.author)
    if (filters.author !== aut) {
      filters.author = aut
      changed = true
    }
  }
  const sDate = query.start_date || query.startDate
  const eDate = query.end_date || query.endDate
  if (sDate && filters.startDate !== String(sDate)) {
    filters.startDate = String(sDate)
    changed = true
  }
  if (eDate && filters.endDate !== String(eDate)) {
    filters.endDate = String(eDate)
    changed = true
  }
  if (query.date) {
    const d = String(query.date)
    if (filters.date !== d) {
      filters.date = d
      filters.startDate = d
      filters.endDate = d
      changed = true
    }
  }
  if (query.q) {
    const q = String(query.q)
    if (filters.q !== q) {
      filters.q = q
      changed = true
    }
  }
  return changed
}

onMounted(() => {
  document.addEventListener('keydown', onListKeydown)
  publishPage('dashboard')
  document.addEventListener('pointerdown', closeViewMenu)
  window.addEventListener('blur', closeViewMenu)
  // Ordering by platform was dropped: a report's name is not a way to navigate.
  if (!sortOptions.some(option => option.value === filters.sort_by)) filters.sort_by = 'date_desc'
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onListKeydown)
  publishPage(null)
  document.removeEventListener('pointerdown', closeViewMenu)
  window.removeEventListener('blur', closeViewMenu)
})

onMounted(async () => {
  loading.value = true
  await ensureServersLoaded()

  // 1. If server changed while away, reset search state
  const currentServerId = activeServer.value?.id || activeServer.value?.url || 'local'
  if (state.searchState.serverId && state.searchState.serverId !== currentServerId) {
    resetFilters()
    currentPage.value = 1
  }

  // 2. Check pending filter from another view (e.g. Statistics page)
  if (state.pendingFilter) {
    const { key, value, startDate, endDate } = state.pendingFilter
    state.pendingFilter = null
    resetFilters()
    if (key === 'author') filters.author = value
    else if (key === 'platform') filters.platform = value
    else if (key === 'protocol') filters.protocols = [value]
    else if (key === 'label' || key === 'tag') filters.labels = [value]
    else if (key === 'date') {
      filters.date = value
      filters.startDate = value
      filters.endDate = value
    } else if (key === 'dateRange') {
      filters.startDate = startDate || value?.startDate || ''
      filters.endDate = endDate || value?.endDate || ''
      filters.date = (filters.startDate && filters.endDate && filters.startDate === filters.endDate) ? filters.startDate : ''
    }
    currentPage.value = 1
  } else {
    // 3. Sync from route query if parameters are specified
    const routeChanged = syncFiltersFromRoute(route.query)
    if (routeChanged) {
      currentPage.value = 1
    }
  }

  await refreshData(true)
})

watch(
  () => [currentPage.value, pageSize.value],
  ([p, s]) => {
    if (state.searchState) {
      state.searchState.currentPage = p
      state.searchState.pageSize = s
      persistSearchState()
    }
  }
)

watch(
  () => route.query,
  (newQuery) => {
    if (syncFiltersFromRoute(newQuery)) {
      currentPage.value = 1
      clearCache()
      fetchReports(1, false)
      fetchFilteredStats()
    }
  },
  { deep: true }
)

watch(
  () => [state.activeServer?.id, state.activeServer?.url, state.serverDataVersion],
  async ([newId, newUrl, newVer], [oldId, oldUrl, oldVer]) => {
    if (newId !== oldId || newUrl !== oldUrl || newVer !== oldVer) {
      if (newId !== oldId || newUrl !== oldUrl) {
        resetFilters()
      }
      reports.value = []
      totalReports.value = 0
      currentPage.value = 1
      clearSelection()
      filterStats.value = null
      filteredStats.value = null
      clearCache()
      loading.value = true
      connectionError.value = null
      await refreshData()
    }
  }
)

let searchDebounceTimeout = null
watch(
  () => filters.q,
  () => {
    if (searchDebounceTimeout) clearTimeout(searchDebounceTimeout)
    searchDebounceTimeout = setTimeout(() => {
      currentPage.value = 1
      clearCache()
      fetchReports(1, false)
      fetchFilteredStats()
    }, 200)
  }
)

watch(
  () => filters.sort_by,
  () => {
    currentPage.value = 1
    clearCache()
    fetchReports(1, false)
    fetchFilteredStats()
  }
)
</script>
