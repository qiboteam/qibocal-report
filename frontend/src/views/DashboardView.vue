<template>
  <div class="flex h-screen overflow-hidden bg-[#f7f7f7]">
    <!-- Left Sidebar -->
    <sidebar
      :filter-stats="filterStats"
      :selected-author="filters.author"
      :selected-protocols="filters.protocols"
      :selected-labels="filters.labels"
      :selected-count="selectedReports.length"
      @update-filter="onUpdateFilter"
      @toggle-protocol="onToggleProtocol"
      @toggle-label="onToggleLabel"
      @reset-filters="onResetFilters"
      @open-label="openLabelModal"
      @open-unlabel="openUnlabelModal"
      @open-author="() => openAuthorModal()"
      @open-delete="openDeleteModal"
      @clear-selection="clearSelection"
    />

    <!-- Main Content Panel -->
    <main class="flex-1 flex flex-col min-w-0 overflow-y-auto">
      <!-- Top Bar: Search, View Mode Switcher, Active Server info -->
      <div class="sticky top-0 bg-[#f7f7f7]/90 backdrop-blur-md px-6 py-4 border-b border-gray-200/70 z-20">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <!-- Full-text search input -->
          <div class="relative flex-1 max-w-md">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              v-model="filters.q"
              type="text"
              placeholder="Search reports by platform, tags, protocols, author..."
              class="w-full pl-9 pr-4 py-2 bg-white rounded-xl text-xs sm:text-sm border-0 focus:outline-none focus:ring-2 focus:ring-[#833dff] shadow-xs"
            />
          </div>

          <!-- Controls: View Mode & Sort -->
          <div class="flex items-center gap-2">
            <!-- Sort dropdown -->
            <select
              v-model="filters.sort_by"
              class="text-xs py-2 px-3 bg-white border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#833dff] text-gray-700 shadow-xs"
            >
              <option value="date_desc">Newest first</option>
              <option value="date_asc">Oldest first</option>
              <option value="platform">Platform A-Z</option>
            </select>

            <!-- Visualization Mode Switcher: Table vs Cards -->
            <div class="flex items-center bg-white p-0.5 rounded-xl border border-gray-200 shadow-xs">
              <button
                @click="viewMode = 'table'"
                class="p-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1"
                :class="viewMode === 'table' ? 'bg-[#ebe0ff] text-[#833dff]' : 'text-gray-500 hover:text-gray-800'"
                title="Table view (Default)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
              <button
                @click="viewMode = 'cards'"
                class="p-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1"
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

        <!-- Active Filter Pills -->
        <div v-if="hasActiveFilters" class="flex flex-wrap items-center gap-1.5 mt-2.5">
          <span class="text-[11px] text-gray-500 font-medium">Active Filters:</span>
          <span
            v-if="filters.author"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800"
          >
            Author: {{ filters.author }}
            <button type="button" @click="filters.author = ''; fetchReports()" class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-black cursor-pointer leading-none">&times;</button>
          </span>
          <span
            v-if="filters.platform"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
          >
            Platform: {{ filters.platform }}
            <button type="button" @click="filters.platform = ''; fetchReports()" class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-black cursor-pointer leading-none">&times;</button>
          </span>
          <span
            v-for="p in filters.protocols"
            :key="p"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
          >
            {{ p }}
            <button type="button" @click="onToggleProtocol(p)" class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-black cursor-pointer leading-none">&times;</button>
          </span>
          <span
            v-for="l in filters.labels"
            :key="l"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
          >
            Tag: {{ l }}
            <button type="button" @click="onToggleLabel(l)" class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-black cursor-pointer leading-none">&times;</button>
          </span>
          <span
            v-if="filters.date"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
          >
            Date: {{ filters.date }}
            <button type="button" @click="filters.date = ''; fetchReports()" class="bg-transparent hover:bg-transparent p-0 border-0 outline-none hover:text-black cursor-pointer leading-none">&times;</button>
          </span>
        </div>
      </div>

      <!-- Main Results Area -->
      <div class="p-6">
        <!-- Results Count & Active Server Indicator -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div class="flex items-center gap-3">
            <h2 class="text-sm font-bold text-gray-700 uppercase tracking-wider">
              Calibration Reports <span v-if="!loading">({{ totalReports }})</span><span v-else class="text-gray-400 font-normal text-xs font-mono">(loading...)</span>
            </h2>
            <div
              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs bg-white border border-gray-200 shadow-2xs"
              :title="activeServer?.url || 'Local Instance'"
            >
              <span
                class="w-2 h-2 rounded-full"
                :class="connectionError ? 'bg-red-500' : loading ? 'bg-amber-400 animate-pulse' : 'bg-emerald-500'"
              ></span>
              <span class="text-gray-400 text-[11px]">Server:</span>
              <span class="font-semibold text-gray-700 max-w-[120px] sm:max-w-[200px] truncate">
                {{ activeServer?.name || 'Local Instance' }}
              </span>
              <span class="text-[10px] font-mono text-gray-400 max-w-[150px] sm:max-w-[220px] truncate hidden sm:inline">
                ({{ activeServer?.url || 'local' }})
              </span>
            </div>
          </div>
          <span v-if="loading" class="text-xs text-purple-600 font-medium animate-pulse">Loading reports...</span>
          <span v-else-if="totalReports > 0" class="text-xs text-gray-400">Page {{ currentPage }} of {{ totalPages }}</span>
          <span v-else class="text-xs text-gray-400">0 matches</span>
        </div>

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

        <!-- Loading State -->
        <div
          v-if="loading"
          class="bg-white rounded-2xl p-12 text-center border border-gray-200 shadow-sm max-w-lg mx-auto my-8 flex flex-col items-center justify-center animate-fade-in"
        >
          <div class="w-8 h-8 border-3 border-[#833dff] border-t-transparent rounded-full animate-spin mb-3"></div>
          <h3 class="font-semibold text-sm text-gray-900">Loading calibration reports...</h3>
          <p class="text-xs text-gray-500 mt-1">
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
          @filter-tag="onToggleLabel"
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
          @filter-tag="onToggleLabel"
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
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { state, addToHistory, apiFetch, ensureServersLoaded } from '../store.js'
import { useReportFilters } from '../composables/useReportFilters.js'
import { usePagination } from '../composables/usePagination.js'
import { useBulkActions } from '../composables/useBulkActions.js'
import Sidebar from '../components/Sidebar.vue'
import ReportTable from '../components/ReportTable.vue'
import ReportCards from '../components/ReportCards.vue'
import PaginationBar from '../components/PaginationBar.vue'
import LabelModal from '../components/modals/LabelModal.vue'
import UnlabelModal from '../components/modals/UnlabelModal.vue'
import AuthorModal from '../components/modals/AuthorModal.vue'
import DeleteConfirmModal from '../components/modals/DeleteConfirmModal.vue'

const router = useRouter()
const route = useRoute()
const viewMode = ref('table')
const reports = ref([])
const filterStats = ref(null)
const loading = ref(true)
const connectionError = ref(null)

const activeServer = computed(() => state.activeServer)

// Composables
const {
  filters,
  hasActiveFilters,
  toggleProtocol,
  toggleLabel,
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
} = usePagination(10)

const {
  selectedReports,
  bulkActionInProgress,
  bulkError,
  bulkSuccessMessage,
  showLabelModal,
  showUnlabelModal,
  showAuthorModal,
  showDeleteModal,
  targetReportIdForAuthor,
  authorInitialValue,
  toggleSelect,
  toggleSelectAll,
  clearSelection,
  openLabelModal,
  openUnlabelModal,
  openAuthorModal,
  openDeleteModal,
  applyBulkLabel,
  applyBulkUnlabel,
  applyAuthor,
  applyBulkDelete,
  removeTagFromReport
} = useBulkActions()

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

const authorSuggestions = computed(() => {
  const authors = new Set()
  if (activeServer.value?.author_identities) {
    for (const canonical of Object.keys(activeServer.value.author_identities)) {
      authors.add(canonical)
    }
  }
  if (filterStats.value?.authors && Array.isArray(filterStats.value.authors)) {
    for (const a of filterStats.value.authors) {
      if (a && a !== 'Unknown') authors.add(a)
    }
  }
  return Array.from(authors)
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

function onPageSizeChange(newSize) {
  pageSize.value = newSize
  currentPage.value = 1
  clearCache()
  fetchReports(1, false)
}

function onUpdateFilter(payload) {
  updateFilter(payload)
  currentPage.value = 1
  clearCache()
  fetchReports(1, false)
}

function onToggleProtocol(p) {
  toggleProtocol(p)
  currentPage.value = 1
  clearCache()
  fetchReports(1, false)
}

function onToggleLabel(l) {
  toggleLabel(l)
  currentPage.value = 1
  clearCache()
  fetchReports(1, false)
}

function onResetFilters() {
  resetFilters()
  clearSelection()
  currentPage.value = 1
  clearCache()
  fetchReports(1, false)
}

function openReport(report) {
  state.currentReportId = report.id
  addToHistory(report)
  router.push(`/reports/${report.id}`)
}

async function onBulkActionSuccess() {
  clearCache()
  await Promise.all([fetchStats(), fetchReports(currentPage.value, false)])
}

async function refreshData() {
  loading.value = true
  connectionError.value = null
  reports.value = []
  totalReports.value = 0
  currentPage.value = 1
  filterStats.value = null
  clearCache()
  await Promise.all([fetchStats(), fetchReports(1, false)])
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
    if (filters.date) {
      params.set('start_date', filters.date)
      params.set('end_date', filters.date)
    }
    filters.protocols.forEach(p => params.append('protocol', p))
    filters.labels.forEach(l => params.append('label', l))

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
      connectionError.value = `Could not connect to ${activeServer.value?.name || 'server'} (${activeServer.value?.url || ''}): ${err.message || 'Network error'}`
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
  if (query.date) {
    const d = String(query.date)
    if (filters.date !== d) {
      filters.date = d
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
  syncFiltersFromRoute(route.query)
  loading.value = true
  await ensureServersLoaded()
  await refreshData()
})

watch(
  () => route.query,
  (newQuery) => {
    if (syncFiltersFromRoute(newQuery)) {
      currentPage.value = 1
      clearCache()
      fetchReports(1, false)
    }
  },
  { deep: true }
)

watch(
  () => [state.activeServer?.id, state.activeServer?.url],
  async ([newId, newUrl], [oldId, oldUrl]) => {
    if (newId !== oldId || newUrl !== oldUrl) {
      reports.value = []
      totalReports.value = 0
      currentPage.value = 1
      clearSelection()
      filterStats.value = null
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
    }, 200)
  }
)

watch(
  () => filters.sort_by,
  () => {
    currentPage.value = 1
    clearCache()
    fetchReports(1, false)
  }
)
</script>
