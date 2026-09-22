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

            <!-- Summary / Recap Toggle Button (InspireHEP style) -->
            <button
              @click="showRecap = !showRecap"
              class="px-2.5 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 shadow-2xs border cursor-pointer shrink-0"
              :class="showRecap ? 'bg-[#ebe0ff] text-[#833dff] border-purple-200' : 'bg-white text-gray-600 border-gray-200 hover:text-gray-900'"
              :title="showRecap ? 'Hide statistics summary' : 'Show statistics summary'"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Summary</span>
              <span v-if="hasActiveFilters" class="w-1.5 h-1.5 rounded-full bg-[#833dff]"></span>
            </button>

            <!-- Sort dropdown -->
            <select
              v-model="filters.sort_by"
              class="text-xs py-2 px-2.5 bg-white border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#833dff] text-gray-700 shadow-xs shrink-0 cursor-pointer"
            >
              <option value="date_desc">Newest first</option>
              <option value="date_asc">Oldest first</option>
              <option value="platform">Platform A-Z</option>
            </select>

            <!-- Visualization Mode Switcher: Table vs Cards -->
            <div class="flex items-center bg-white p-0.5 rounded-xl border border-gray-200 shadow-xs shrink-0">
              <button
                @click="viewMode = 'table'"
                class="p-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1 cursor-pointer"
                :class="viewMode === 'table' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-500 hover:text-gray-800'"
                title="Table view (Default)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
              <button
                @click="viewMode = 'cards'"
                class="p-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1 cursor-pointer"
                :class="viewMode === 'cards' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-500 hover:text-gray-800'"
                title="Horizontal cards view"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
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
          @select="openReport"
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
          @select="openReport"
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
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { state, addToHistory, apiFetch, ensureServersLoaded, resolveAuthor, persistSearchState } from '../store.js'
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
const reports = ref([])
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
      for (const t of (r.tags || r.labels || [])) {
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

function prefetchAccessiblePages() {
  const targetPages = getAccessiblePages(currentPage.value, totalPages.value)
  const qKey = getCurrentFilterKey()
  for (const p of targetPages) {
    const key = getCacheKey(qKey, p)
    if (!hasInCache(key)) {
      fetchReports(p, true)
    }
  }
}

function goToPage(p) {
  if (p < 1 || p > totalPages.value || p === currentPage.value) return
  fetchReports(p, false)
}

function applyFilterChange(changeFn) {
  if (changeFn) changeFn()
  currentPage.value = 1
  clearCache()
  fetchReports(1, false)
  fetchFilteredStats()
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
    filters.labels.forEach(l => params.append('label', l))
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

function openReport(report, targetProtocol = null) {
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
  openReport(report, protocol)
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
  loading.value = true
  connectionError.value = null
  reports.value = []
  totalReports.value = 0
  const targetPage = preservePage ? (currentPage.value || 1) : 1
  currentPage.value = targetPage
  filterStats.value = null
  filteredStats.value = null
  clearCache()
  await Promise.all([fetchStats(), fetchReports(targetPage, false)])
  await fetchFilteredStats()
}

async function fetchStats() {
  try {
    const res = await apiFetch('/api/reports/stats')
    if (res.ok) {
      filterStats.value = await res.json()
    } else {
      filterStats.value = null
    }
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
    filters.labels.forEach(l => params.append('label', l))
    filters.qubits?.forEach(q => params.append('qubit', q))

    // 1. Try backend /api/reports/stats endpoint
    let statsData = null
    try {
      const res = await apiFetch(`/api/reports/stats?${params.toString()}`)
      if (res.ok) {
        statsData = await res.json()
      }
    } catch {
      statsData = null
    }

    // 2. Verify if the returned stats actually reflect the filter.
    // If backend ignored query parameters, statsData.total_reports will equal fullStats.total_reports
    // while totalReports.value is smaller, or it won't respect active criteria.
    const fullTotal = filterStats.value?.total_reports ?? 0
    const isHonored = Boolean(
      statsData &&
      (fullTotal === 0 || totalReports.value === 0 || statsData.total_reports === totalReports.value || statsData.total_reports < fullTotal) &&
      (!filters.platform || statsData.platforms.every(p => p.name === filters.platform)) &&
      (!filters.author || statsData.authors.every(a => a === filters.author)) &&
      (!start || statsData.date_histogram.every(d => d.date >= start)) &&
      (!end || statsData.date_histogram.every(d => d.date <= end))
    )

    if (isHonored) {
      filteredStats.value = statsData
      return
    }

    // 3. Fallback: Fetch all matching reports from /api/reports (unpaginated) and compute stats client-side.
    // This is 100% reliable across all servers and dev setups.
    const reportsRes = await apiFetch(`/api/reports?${params.toString()}`)
    if (reportsRes.ok) {
      const data = await reportsRes.json()
      const items = Array.isArray(data) ? data : (data.items || [])
      filteredStats.value = computeStatsFromReports(items)
    } else {
      filteredStats.value = null
    }
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
    const params = new URLSearchParams()
    params.set('page', String(page))
    params.set('page_size', String(pageSize.value))
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
    filters.labels.forEach(l => params.append('label', l))
    filters.qubits?.forEach(q => params.append('qubit', q))

    const res = await apiFetch(`/api/reports?${params.toString()}`)
    if (res.ok) {
      const data = await res.json()
      const items = Array.isArray(data) ? data : (data.items || [])
      const total = Array.isArray(data) ? data.length : (data.total ?? items.length)
      const total_pages = Array.isArray(data) ? 1 : (data.total_pages ?? 1)
      const page_num = Array.isArray(data) ? 1 : (data.page ?? page)

      const payload = {
        items,
        total,
        total_pages,
        page: page_num,
        page_size: pageSize.value
      }

      setCache(cacheKey, payload)

      if (!isPrefetch) {
        reports.value = items
        totalReports.value = total
        totalPages.value = total_pages
        currentPage.value = page_num
        loading.value = false
        prefetchAccessiblePages()
      }
    } else if (!isPrefetch) {
      connectionError.value = `Server responded with status ${res.status}`
      reports.value = []
      loading.value = false
    }
  } catch (err) {
    if (!isPrefetch) {
      console.error('Failed to fetch reports', err)
      if (!activeServer.value && (!state.servers || state.servers.length === 0)) {
        connectionError.value = null
      } else {
        connectionError.value = `Could not connect to ${activeServer.value?.name || 'server'} (${activeServer.value?.url || ''}): ${err.message || 'Network error'}`
      }
      reports.value = []
      loading.value = false
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
