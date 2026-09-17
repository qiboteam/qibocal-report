<template>
  <div class="flex h-screen overflow-hidden bg-[#f7f7f7]">
    <!-- Left Sidebar with Protocols Summary in lower half -->
    <sidebar
      :report-protocols="protocols"
      :regenerating="regenerating"
      @regenerate="handleRegenerate"
      @print-pdf="handlePrintPDF"
    />

    <!-- Main Report Visualization Panel -->
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
          <button @click="loadReportData" class="px-3 py-1.5 bg-white border border-red-200 text-red-700 rounded-lg text-xs font-semibold hover:bg-red-50 transition cursor-pointer">
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

          <!-- Actions: Print to PDF & Regenerate plots -->
          <div class="flex items-center gap-2">
            <!-- Regenerate button -->
            <button
              @click="handleRegenerate"
              :disabled="regenerating"
              class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-white border border-gray-200 hover:border-purple-300 text-gray-700 shadow-2xs flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
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

            <!-- Print to PDF button -->
            <button
              @click="handlePrintPDF"
              class="px-3.5 py-1.5 rounded-xl text-xs font-semibold bm-btn-primary shadow-2xs flex items-center gap-1.5 cursor-pointer"
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
          <button @click="statusBanner = ''" class="text-purple-600 hover:text-purple-900 cursor-pointer">&times;</button>
        </div>

        <!-- Report Header Card -->
        <report-header-card
          :report="report"
          :saving-author="savingAuthor"
          @remove-tag="handleRemoveTag"
          @save-author="handleSaveAuthor"
        />

        <!-- Collapsible Platform Snapshot Card -->
        <platform-snapshot-card
          v-if="report.platform_snapshot"
          :snapshot="report.platform_snapshot"
        />

        <!-- Protocols List with Figures -->
        <div class="space-y-6">
          <protocol-card
            v-for="(proto, idx) in protocols"
            :key="proto.id"
            :proto="proto"
            :index="idx"
          />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { state, ensureServersLoaded } from '../store.js'
import { useReportDetail } from '../composables/useReportDetail.js'
import Sidebar from '../components/Sidebar.vue'
import ReportHeaderCard from '../components/report/ReportHeaderCard.vue'
import PlatformSnapshotCard from '../components/report/PlatformSnapshotCard.vue'
import ProtocolCard from '../components/report/ProtocolCard.vue'

const route = useRoute()
const reportId = computed(() => route.params.id)
const activeServer = computed(() => state.activeServer)

const {
  loading,
  loadingStatus,
  error,
  report,
  protocols,
  regenerating,
  statusBanner,
  savingAuthor,
  loadReportData,
  handleRegenerate,
  handleSaveAuthor,
  handleRemoveTag
} = useReportDetail(reportId)

function handlePrintPDF() {
  window.print()
}

onMounted(async () => {
  await ensureServersLoaded()
  await loadReportData()
})

watch(
  () => route.params.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      loadReportData()
    }
  }
)

watch(
  () => [state.activeServer?.id, state.activeServer?.url],
  ([newId, newUrl], [oldId, oldUrl]) => {
    if (newId !== oldId || newUrl !== oldUrl) {
      loadReportData()
    }
  }
)
</script>
