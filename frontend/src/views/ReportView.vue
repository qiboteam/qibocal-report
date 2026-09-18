<template>
  <div class="flex h-screen overflow-hidden bg-[#f7f7f7]">
    <!-- Left Sidebar with Protocols Summary in lower half -->
    <sidebar
      :report-protocols="protocols"
      :report-id="reportId"
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
          <button
            type="button"
            @click="goBackToSearch"
            class="inline-block px-3 py-1.5 bg-red-100 text-red-800 rounded-lg text-xs font-semibold cursor-pointer hover:bg-red-200 transition"
          >
            Back to Search
          </button>
          <button @click="loadReportData" class="px-3 py-1.5 bg-white border border-red-200 text-red-700 rounded-lg text-xs font-semibold hover:bg-red-50 transition cursor-pointer">
            Retry
          </button>
        </div>
      </div>

      <div v-else-if="report" class="max-w-5xl mx-auto space-y-6">
        <!-- Top Navigation / Action Bar (hidden when printing) -->
        <div class="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-gray-200">
          <button
            type="button"
            @click="goBackToSearch"
            class="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-600 hover:text-[#833dff] transition cursor-pointer group"
            title="Back to search (filters preserved)"
          >
            <svg class="w-4 h-4 text-gray-500 group-hover:text-[#833dff] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>Back to Search</span>
            <span
              v-if="hasActiveSearch"
              class="px-1.5 py-0.5 rounded-full text-[10px] font-mono bg-purple-100 text-purple-700 font-medium"
            >
              Filtered
            </span>
          </button>

          <!-- Actions: Print to PDF & Regenerate plots -->
          <div class="flex items-center gap-2">
            <!-- Docs Index button -->
            <button
              type="button"
              @click="showDocsModal = true"
              class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-white border border-gray-200 hover:border-purple-300 text-gray-700 shadow-2xs flex items-center gap-1.5 transition cursor-pointer"
              title="Edit custom protocol documentation mappings for this server"
            >
              <svg class="w-3.5 h-3.5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <span>Docs Index</span>
            </button>

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

        <!-- Protocols List with Figures -->
        <div class="space-y-6">
          <protocol-card
            v-for="(proto, idx) in protocols"
            :key="proto.id"
            :proto="proto"
            :index="idx"
            :report-id="reportId"
          />
        </div>
      </div>
    </main>

    <!-- Protocol Documentation Mapping Modal -->
    <protocol-docs-modal
      :show="showDocsModal"
      @close="showDocsModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { state, ensureServersLoaded, hasActiveSearchFilters } from '../store.js'
import { useReportDetail } from '../composables/useReportDetail.js'
import Sidebar from '../components/Sidebar.vue'
import ReportHeaderCard from '../components/report/ReportHeaderCard.vue'
import ProtocolCard from '../components/report/ProtocolCard.vue'
import ProtocolDocsModal from '../components/modals/ProtocolDocsModal.vue'

const showDocsModal = ref(false)

const route = useRoute()
const router = useRouter()
const reportId = computed(() => route.params.id)
const activeServer = computed(() => state.activeServer)

const hasActiveSearch = computed(() => {
  return hasActiveSearchFilters(state.searchState?.filters)
})

function goBackToSearch() {
  router.push('/dashboard')
}

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

function scrollToProtocol(protoId) {
  if (!protoId) return
  const cleanId = String(protoId).toLowerCase().trim()
  let el = document.getElementById(`proto-${protoId}`) || document.getElementById(`proto-${cleanId}`)
  if (!el && protocols.value?.length) {
    const matched = protocols.value.find(
      p => p.id?.toLowerCase() === cleanId || p.name?.toLowerCase() === cleanId
    )
    if (matched) {
      el = document.getElementById(`proto-${matched.id}`)
    }
  }
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}

async function handlePrintPDF() {
  window.dispatchEvent(new Event('resize'))
  await new Promise(r => setTimeout(r, 120))
  window.print()
}

onMounted(async () => {
  await ensureServersLoaded()
  await loadReportData()
})

watch(
  () => [loading.value, route.query.protocol],
  ([isLoading, targetProto]) => {
    if (!isLoading && targetProto) {
      setTimeout(() => {
        scrollToProtocol(targetProto)
      }, 150)
    }
  },
  { immediate: true }
)

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
