<template>
  <div class="flex h-screen overflow-hidden bg-[#f7f7f7]">
    <!-- Left Sidebar (Issue #3) -->
    <sidebar 
      :filter-stats="filterStats"
      :selected-author="filters.author"
      :selected-protocols="filters.protocols"
      :selected-labels="filters.labels"
      @update-filter="onUpdateFilter"
      @toggle-protocol="toggleProtocol"
      @toggle-label="toggleLabel"
      @reset-filters="resetFilters"
    />

    <!-- Main Content Panel (Issue #3) -->
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
              @input="fetchReports"
              type="text"
              placeholder="Search reports by title, platform, author, tag..."
              class="w-full pl-9 pr-4 py-2 bg-white rounded-xl text-xs sm:text-sm border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#833dff] focus:border-transparent shadow-xs"
            />
          </div>

          <!-- Controls: View Mode & Sort -->
          <div class="flex items-center gap-2">
            <!-- Sort dropdown -->
            <select 
              v-model="filters.sort_by"
              @change="fetchReports"
              class="text-xs py-2 px-3 bg-white border border-gray-200 rounded-xl focus:outline-none text-gray-700 shadow-xs"
            >
              <option value="date_desc">Newest first</option>
              <option value="date_asc">Oldest first</option>
              <option value="title">Title A-Z</option>
            </select>

            <!-- Visualization Mode Switcher: Table (default) vs Cards (Issue #3) -->
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
                title="Horizontal cards view (Inspire style)"
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
            <button @click="filters.author = ''; fetchReports()" class="hover:text-black">&times;</button>
          </span>
          <span 
            v-for="p in filters.protocols" 
            :key="p"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
          >
            {{ p }}
            <button @click="toggleProtocol(p)" class="hover:text-black">&times;</button>
          </span>
          <span 
            v-for="l in filters.labels" 
            :key="l"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-gray-200 text-gray-800"
          >
            #{{ l }}
            <button @click="toggleLabel(l)" class="hover:text-black">&times;</button>
          </span>
          <span 
            v-if="filters.date" 
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800 font-mono"
          >
            Date: {{ filters.date }}
            <button @click="filters.date = ''; fetchReports()" class="hover:text-black">&times;</button>
          </span>
        </div>
      </div>

      <!-- Main Results Area -->
      <div class="p-6">
        <!-- Results Count -->
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-bold text-gray-700 uppercase tracking-wider">
            Calibration Reports ({{ reports.length }})
          </h2>
          <span class="text-xs text-gray-400">Showing all matches</span>
        </div>

        <!-- Empty State -->
        <div 
          v-if="reports.length === 0" 
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
            @click="resetFilters" 
            class="mt-4 px-4 py-2 rounded-xl text-xs font-semibold bm-btn-secondary"
          >
            Reset All Filters
          </button>
        </div>

        <!-- Table View (Default, Issue #3) -->
        <report-table 
          v-else-if="viewMode === 'table'"
          :reports="reports"
          @select="openReport"
        />

        <!-- Full-size Horizontal Cards View (Inspire style, Issue #3) -->
        <report-cards 
          v-else
          :reports="reports"
          @select="openReport"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { state, addToHistory } from '../store.js'
import Sidebar from '../components/Sidebar.vue'
import ReportTable from '../components/ReportTable.vue'
import ReportCards from '../components/ReportCards.vue'

const router = useRouter()
const viewMode = ref('table') // default table
const reports = ref([])
const filterStats = ref(null)

const filters = reactive({
  q: '',
  author: '',
  date: '',
  protocols: [],
  labels: [],
  sort_by: 'date_desc'
})

const hasActiveFilters = computed(() => {
  return filters.author || filters.date || filters.protocols.length > 0 || filters.labels.length > 0
})

onMounted(async () => {
  await fetchStats()
  await fetchReports()
})

async function fetchStats() {
  try {
    const res = await fetch('/api/reports/stats')
    if (res.ok) {
      filterStats.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to fetch stats', err)
  }
}

async function fetchReports() {
  try {
    const params = new URLSearchParams()
    if (filters.q) params.set('q', filters.q)
    if (filters.author) params.set('author', filters.author)
    if (filters.date) {
      params.set('start_date', filters.date)
      params.set('end_date', filters.date)
    }
    if (filters.sort_by) params.set('sort_by', filters.sort_by)
    filters.protocols.forEach(p => params.append('protocol', p))
    filters.labels.forEach(l => params.append('label', l))

    const res = await fetch(`/api/reports?${params.toString()}`)
    if (res.ok) {
      reports.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to fetch reports', err)
  }
}

function onUpdateFilter({ key, value }) {
  if (key === 'author') filters.author = value
  if (key === 'date') filters.date = value
  fetchReports()
}

function toggleProtocol(name) {
  const idx = filters.protocols.indexOf(name)
  if (idx >= 0) filters.protocols.splice(idx, 1)
  else filters.protocols.push(name)
  fetchReports()
}

function toggleLabel(name) {
  const idx = filters.labels.indexOf(name)
  if (idx >= 0) filters.labels.splice(idx, 1)
  else filters.labels.push(name)
  fetchReports()
}

function resetFilters() {
  filters.q = ''
  filters.author = ''
  filters.date = ''
  filters.protocols = []
  filters.labels = []
  fetchReports()
}

function openReport(report) {
  state.currentReportId = report.id
  addToHistory(report)
  router.push(`/reports/${report.id}`)
}
</script>
