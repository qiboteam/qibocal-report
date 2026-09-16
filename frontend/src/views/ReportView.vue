<template>
  <div class="flex h-screen overflow-hidden bg-[#f7f7f7]">
    <!-- Left Sidebar with Protocols Summary in lower half (Issue #3) -->
    <sidebar 
      :report-protocols="protocols"
    />

    <!-- Main Report Visualization Panel (Issue #3, #10) -->
    <main class="flex-1 overflow-y-auto p-4 sm:p-8 report-print-container">
      <div v-if="loading" class="flex flex-col items-center justify-center h-64">
        <div class="w-8 h-8 border-3 border-[#833dff] border-t-transparent rounded-full animate-spin"></div>
        <p class="mt-3 text-xs text-gray-500 font-medium">Loading report artifacts...</p>
      </div>

      <div v-else-if="error" class="bg-red-50 text-red-700 p-6 rounded-2xl border border-red-200">
        <h3 class="font-bold text-base">Unable to load report</h3>
        <p class="text-xs mt-1">{{ error }}</p>
        <router-link to="/dashboard" class="inline-block mt-3 px-3 py-1.5 bg-red-100 rounded-lg text-xs font-semibold">
          Back to Dashboard
        </router-link>
      </div>

      <div v-else-if="report" class="max-w-5xl mx-auto space-y-6">
        <!-- Top Navigation / Action Bar (hidden when printing) -->
        <div class="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-gray-200">
          <router-link 
            to="/dashboard"
            class="inline-flex items-center gap-1 text-xs font-semibold text-gray-600 hover:text-[#833dff] transition"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Search
          </router-link>

          <!-- Actions: Print to PDF & Regenerate plots (Issue #3, #10) -->
          <div class="flex items-center gap-2">
            <!-- Regenerate button -->
            <button 
              @click="handleRegenerate"
              :disabled="regenerating"
              class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-white border border-gray-200 hover:border-purple-300 text-gray-700 shadow-2xs flex items-center gap-1.5 transition disabled:opacity-50"
              title="Delete cached plots and re-evaluate protocols"
            >
              <svg 
                class="w-3.5 h-3.5 text-[#833dff]" 
                :class="regenerating ? 'animate-spin' : ''"
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {{ regenerating ? 'Regenerating...' : 'Regenerate Plots' }}
            </button>

            <!-- Print to PDF button (Issue #3) -->
            <button 
              @click="handlePrintPDF"
              class="px-3.5 py-1.5 rounded-xl text-xs font-semibold bm-btn-primary shadow-2xs flex items-center gap-1.5"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              Print to PDF
            </button>
          </div>
        </div>

        <!-- Notification if regenerated -->
        <div 
          v-if="statusBanner" 
          class="no-print p-3 bg-purple-50 border border-purple-200 rounded-xl text-xs text-purple-900 flex items-center justify-between"
        >
          <span>✓ {{ statusBanner }}</span>
          <button @click="statusBanner = ''" class="text-purple-600 hover:text-purple-900">&times;</button>
        </div>

        <!-- Report Header Card -->
        <div class="bm-card p-6 border border-gray-100">
          <div class="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-gray-100">
            <div>
              <!-- Serif font for H1 per Issue #2 -->
              <h1 class="text-2xl sm:text-3xl text-gray-900">
                {{ report.title }}
              </h1>
              <p class="text-xs font-mono text-gray-400 mt-1">ID: {{ report.id }}</p>
            </div>

            <div class="flex items-center gap-2">
              <span class="px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">
                {{ report.platform }}
              </span>
              <span 
                v-if="report.has_cached_report" 
                class="px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider uppercase bg-emerald-100 text-emerald-800"
              >
                Pre-cached
              </span>
            </div>
          </div>

          <!-- Metadata Grid -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 text-xs">
            <div>
              <span class="text-gray-400 block mb-0.5">Author</span>
              <strong class="text-gray-800">{{ report.author }}</strong>
            </div>
            <div>
              <span class="text-gray-400 block mb-0.5">Execution Date</span>
              <strong class="text-gray-800 font-mono">{{ report.date }} {{ report.time }}</strong>
            </div>
            <div>
              <span class="text-gray-400 block mb-0.5">Total Duration</span>
              <strong class="text-gray-800 font-mono">{{ report.total_execution_time || 'N/A' }}</strong>
            </div>
            <div>
              <span class="text-gray-400 block mb-0.5">Target Qubits</span>
              <strong class="text-gray-800 font-mono">Q{{ report.targets.join(', Q') }}</strong>
            </div>
          </div>

          <!-- Tags & Git Commit -->
          <div v-if="report.labels?.length || report.history?.git_commit" class="mt-4 pt-3 border-t border-gray-50 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="text-gray-400">Labels:</span>
              <span v-for="l in report.labels" :key="l" class="bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                #{{ l }}
              </span>
            </div>
            <div v-if="report.history?.git_commit" class="font-mono text-[11px] text-gray-400">
              commit: {{ report.history.git_commit }}
            </div>
          </div>
        </div>

        <!-- Collapsible Platform Snapshot Card -->
        <div v-if="hasPlatformData" class="bm-card overflow-hidden border border-gray-100">
          <button 
            @click="platformAccordionOpen = !platformAccordionOpen"
            class="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50/70 transition"
          >
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-[#833dff]"></span>
              <h3 class="text-xs font-bold uppercase tracking-wider text-gray-800">
                Hardware Platform Snapshot
              </h3>
            </div>
            <svg 
              class="w-4 h-4 text-gray-400 transition" 
              :class="platformAccordionOpen ? 'rotate-180' : ''"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div v-if="platformAccordionOpen" class="p-4 border-t border-gray-100 bg-gray-50/50">
            <pre class="p-3 bg-white rounded-xl text-xs font-mono text-gray-700 overflow-x-auto border border-gray-200">{{ JSON.stringify(report.platform_snapshot, null, 2) }}</pre>
          </div>
        </div>

        <!-- Protocols List with HTML & Plotly Figures (Issue #10) -->
        <div class="space-y-6">
          <div 
            v-for="(proto, idx) in protocols" 
            :key="proto.id"
            :id="`proto-${proto.id}`"
            class="bm-card p-6 border border-gray-100 page-break"
          >
            <!-- Protocol Header -->
            <div class="flex items-center justify-between pb-3 border-b border-gray-100">
              <div class="flex items-center gap-2.5">
                <span class="w-6 h-6 rounded-lg bg-purple-100 text-[#833dff] font-bold text-xs flex items-center justify-center font-mono">
                  {{ idx + 1 }}
                </span>
                <h2 class="text-lg font-bold text-gray-900">
                  {{ proto.name }}
                </h2>
              </div>

              <div class="flex items-center gap-2">
                <span class="text-xs font-mono text-gray-400">⏱️ {{ proto.execution_time || 'N/A' }}</span>
                <span class="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
                  {{ proto.status }}
                </span>
              </div>
            </div>

            <!-- Injected Protocol HTML Output (Issue #10) -->
            <div v-if="proto.html" class="my-4" v-html="proto.html"></div>

            <!-- Injected Plotly Figures (Issue #10) -->
            <div v-if="proto.figures && proto.figures.length > 0" class="mt-4 space-y-4">
              <plotly-viewer 
                v-for="fig in proto.figures" 
                :key="fig.id || fig.title"
                :figure="fig"
              />
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { state, addToHistory } from '../store.js'
import Sidebar from '../components/Sidebar.vue'
import PlotlyViewer from '../components/PlotlyViewer.vue'

const route = useRoute()
const loading = ref(true)
const regenerating = ref(false)
const error = ref(null)
const report = ref(null)
const protocols = ref([])
const platformAccordionOpen = ref(false)
const statusBanner = ref('')

const reportId = computed(() => route.params.id)

const hasPlatformData = computed(() => {
  return report.value?.platform_snapshot && Object.keys(report.value.platform_snapshot).length > 0
})

onMounted(async () => {
  await loadReportData()
})

async function loadReportData() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/reports/${reportId.value}`)
    if (!res.ok) throw new Error(`Report not found (${res.status})`)
    const data = await res.json()
    report.value = data
    state.currentReportId = data.id
    addToHistory(data)

    // Load protocol details (HTML + Plotly figures)
    const protoRes = await fetch(`/api/reports/${reportId.value}/protocols`)
    if (protoRes.ok) {
      protocols.value = await protoRes.json()
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function handleRegenerate() {
  regenerating.value = true
  try {
    const res = await fetch(`/api/reports/${reportId.value}/regenerate`, { method: 'POST' })
    if (res.ok) {
      protocols.value = await res.json()
      statusBanner.value = 'Report plots regenerated successfully!'
      report.value.has_cached_report = true
    }
  } catch (err) {
    alert('Regeneration failed: ' + err.message)
  } finally {
    regenerating.value = false
  }
}

function handlePrintPDF() {
  window.print()
}
</script>
