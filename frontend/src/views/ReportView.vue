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
        <p class="mt-3 text-xs text-gray-700 font-medium">{{ loadingStatus }}</p>
        <p class="mt-1 text-[11px] text-gray-400 font-mono">Server is preparing plots in the background...</p>
      </div>

      <div v-else-if="error" class="bg-red-50 text-red-700 p-6 rounded-2xl border border-red-200 max-w-2xl mx-auto my-8">
        <h3 class="font-bold text-base">Unable to load report</h3>
        <p class="text-xs mt-1">{{ error }}</p>
        <p class="text-xs text-gray-500 mt-2 font-mono">Server: {{ activeServer?.name || 'Local Instance' }} ({{ activeServer?.url || 'local' }})</p>
        <div class="flex items-center gap-2 mt-4">
          <router-link to="/dashboard" class="inline-block px-3 py-1.5 bg-red-100 text-red-800 rounded-lg text-xs font-semibold">
            Back to Dashboard
          </router-link>
          <button @click="loadReportData" class="px-3 py-1.5 bg-white border border-red-200 text-red-700 rounded-lg text-xs font-semibold hover:bg-red-50 transition">
            Retry
          </button>
        </div>
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
              <h1 class="text-xl sm:text-2xl font-bold font-mono text-gray-900">
                {{ report.id }}
              </h1>
            </div>

            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">
                {{ report.platform }}
              </span>
              <span
                v-for="t in (report.tags || report.labels || [])"
                :key="t"
                class="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 text-purple-700 font-mono"
              >
                {{ t }}
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
          <div v-if="(report.tags || report.labels)?.length || report.history?.git_commit" class="mt-4 pt-3 border-t border-gray-50 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="text-gray-500 font-semibold">Tags:</span>
              <span
                v-for="l in (report.tags || report.labels || [])"
                :key="l"
                class="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 text-purple-700 font-mono"
              >
                {{ l }}
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
                <span
                  class="px-2 py-0.5 rounded text-xs font-semibold"
                  :class="proto.status === 'error' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'"
                >
                  {{ proto.status }}
                </span>
              </div>
            </div>

            <!-- Error message if plot could not be generated -->
            <div v-if="proto.error" class="my-4 p-4 rounded-xl bg-amber-50/80 border border-amber-200/80 text-amber-900 flex items-start gap-3">
              <span class="text-lg leading-none mt-0.5">⚠️</span>
              <div>
                <p class="font-semibold text-xs tracking-wide uppercase text-amber-950">Plot Unavailable</p>
                <p class="text-xs text-amber-800 mt-0.5 leading-relaxed">{{ proto.error }}</p>
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
            <div v-else-if="!proto.error && !proto.html" class="my-4 text-xs text-gray-400 italic">
              No figures or tables available for this routine.
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { state, addToHistory, apiFetch, getActiveWsUrl, ensureServersLoaded } from '../store.js'
import Sidebar from '../components/Sidebar.vue'
import PlotlyViewer from '../components/PlotlyViewer.vue'

const route = useRoute()
const loading = ref(true)
const loadingStatus = ref('Connecting to server...')
const regenerating = ref(false)
const error = ref(null)
const report = ref(null)
const protocols = ref([])
const platformAccordionOpen = ref(false)
const statusBanner = ref('')

let activeWs = null

const reportId = computed(() => route.params.id)
const activeServer = computed(() => state.activeServer)

const hasPlatformData = computed(() => {
  return report.value?.platform_snapshot && Object.keys(report.value.platform_snapshot).length > 0
})

onMounted(async () => {
  await ensureServersLoaded()
  await loadReportData()
})

watch(
  () => [state.activeServer?.id, state.activeServer?.url],
  async ([newId, newUrl], [oldId, oldUrl]) => {
    if (newId !== oldId || newUrl !== oldUrl) {
      if (activeWs) {
        try { activeWs.close() } catch {}
      }
      await loadReportData()
    }
  }
)

onUnmounted(() => {
  if (activeWs) {
    try { activeWs.close() } catch {}
  }
})

async function loadReportData() {
  loading.value = true
  error.value = null
  loadingStatus.value = 'Connecting to server...'

  // 1. Attempt WebSocket connection for server-initiated streaming
  try {
    const wsOk = await connectWebSocket()
    if (wsOk) return
  } catch (err) {
    console.warn('WebSocket streaming unavailable, falling back to HTTP:', err)
  }

  // 2. Fallback to HTTP if WebSocket cannot connect
  await loadViaHttp()
}

function connectWebSocket() {
  return new Promise((resolve, reject) => {
    const encodedId = encodeURIComponent(reportId.value)
    const wsUrl = getActiveWsUrl(`/ws/reports/${encodedId}`)

    let ws = null
    try {
      ws = new WebSocket(wsUrl)
      activeWs = ws
    } catch (e) {
      reject(e)
      return
    }

    let resolved = false

    // 15-second safety timer before falling back to HTTP
    const timer = setTimeout(() => {
      if (!resolved) {
        resolved = true
        try { ws.close() } catch {}
        reject(new Error('WebSocket connection timed out'))
      }
    }, 15000)

    ws.onopen = () => {
      loadingStatus.value = 'Analyzing report directory...'
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'metadata') {
          report.value = msg.report
          state.currentReportId = msg.report.id
          addToHistory(msg.report)
        } else if (msg.type === 'status') {
          loadingStatus.value = msg.message
        } else if (msg.type === 'progress') {
          loadingStatus.value = msg.message || `Plotting routine (${msg.step}/${msg.total})...`
        } else if (msg.type === 'ready') {
          clearTimeout(timer)
          resolved = true
          protocols.value = msg.protocols
          loading.value = false
          resolve(true)
        } else if (msg.type === 'error') {
          clearTimeout(timer)
          resolved = true
          reject(new Error(msg.message || 'Report not found'))
        }
      } catch (e) {
        console.error('Failed to parse WS payload', e)
      }
    }

    ws.onerror = (e) => {
      if (!resolved) {
        clearTimeout(timer)
        resolved = true
        reject(e)
      }
    }

    ws.onclose = () => {
      if (!resolved && loading.value) {
        clearTimeout(timer)
        resolved = true
        reject(new Error('WebSocket closed before completion'))
      }
    }
  })
}

async function loadViaHttp() {
  try {
    loadingStatus.value = 'Fetching report metadata...'
    const encodedId = encodeURIComponent(reportId.value)
    const res = await apiFetch(`/api/reports/${encodedId}`)
    if (!res.ok) throw new Error(`Report not found (${res.status})`)
    const data = await res.json()
    report.value = data
    state.currentReportId = data.id
    addToHistory(data)

    loadingStatus.value = 'Retrieving report protocols...'
    const protoRes = await apiFetch(`/api/reports/${encodedId}/protocols`)
    if (protoRes.ok) {
      protocols.value = await protoRes.json()
    } else {
      throw new Error(`Failed to load protocols (${protoRes.status})`)
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function handleRegenerate() {
  regenerating.value = true
  statusBanner.value = ''
  try {
    const encodedId = encodeURIComponent(reportId.value)
    const res = await apiFetch(`/api/reports/${encodedId}/regenerate`, { method: 'POST' })
    if (res.ok) {
      protocols.value = await res.json()
      statusBanner.value = 'Report plots regenerated successfully!'
      if (report.value) {
        report.value.has_cached_report = true
      }
    } else {
      throw new Error(`Regeneration failed (${res.status})`)
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
