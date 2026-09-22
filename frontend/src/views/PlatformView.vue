<template>
  <div class="flex h-screen overflow-hidden bg-[#f7f7f7]">
    <!-- Left Sidebar -->
    <sidebar />

    <!-- Main Content Panel -->
    <main class="flex-1 flex flex-col min-w-0 overflow-y-auto">
      <!-- Sticky Top Navigation Bar -->
      <div class="sticky top-0 bg-[#f7f7f7]/95 backdrop-blur-md px-4 sm:px-6 py-3 border-b border-gray-200/80 z-20 flex flex-col gap-3">
        <!-- Row 1: Back to Report & Title -->
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-3 min-w-0">
            <!-- Back to Report -->
            <button
              type="button"
              @click="goBackToReport"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs text-xs font-semibold transition cursor-pointer shrink-0"
              title="Return to report overview"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span>Back to Report</span>
            </button>

            <!-- Breadcrumbs / ID -->
            <div class="min-w-0">
              <div class="flex items-center gap-1.5 text-[11px] text-gray-400 font-mono">
                <span>Platform Navigation</span>
                <span>/</span>
                <span class="text-gray-600 font-semibold truncate">{{ reportId }}</span>
              </div>
            </div>
          </div>

          <!-- Platform Pill & Type Switcher -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">
              {{ platformData?.platform_name || 'Generic QPU' }}
            </span>

            <!-- Old Platform / New Platform Segmented Toggle -->
            <div class="inline-flex p-0.5 bg-gray-200/70 rounded-xl shadow-inner text-xs font-semibold">
              <button
                type="button"
                @click="switchPlatformType('old')"
                class="px-3 py-1 rounded-lg transition-all cursor-pointer"
                :class="activePlatformType === 'old' ? 'bg-white text-[#833dff] shadow-xs' : 'text-gray-600 hover:text-gray-900'"
              >
                Old Platform
              </button>
              <button
                type="button"
                @click="switchPlatformType('new')"
                class="px-3 py-1 rounded-lg transition-all cursor-pointer"
                :class="activePlatformType === 'new' ? 'bg-white text-[#833dff] shadow-xs' : 'text-gray-600 hover:text-gray-900'"
              >
                New Platform
              </button>
            </div>

            <!-- Download Platform Zip -->
            <a
              :href="downloadZipUrl"
              class="px-2.5 py-1 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs text-xs font-semibold inline-flex items-center gap-1.5 transition cursor-pointer"
              title="Download platform directory as zip"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>Download Zip</span>
            </a>
          </div>
        </div>

        <!-- Row 2: File Selector, View Mode & Search Filter -->
        <div class="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-gray-200/60">
          <!-- File Tabs: parameters.json / calibration.json -->
          <div class="flex items-center gap-1.5">
            <button
              type="button"
              @click="activeFile = 'parameters'"
              class="px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1.5"
              :class="activeFile === 'parameters' ? 'bg-[#833dff] text-white shadow-2xs' : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              </svg>
              <span>parameters.json</span>
              <span
                v-if="parametersCount !== null"
                class="px-1.5 py-0.2 rounded-full text-[10px] font-mono"
                :class="activeFile === 'parameters' ? 'bg-purple-700/60 text-white' : 'bg-gray-100 text-gray-600'"
              >
                {{ parametersCount }}
              </span>
            </button>

            <button
              type="button"
              @click="activeFile = 'calibration'"
              class="px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1.5"
              :class="activeFile === 'calibration' ? 'bg-[#833dff] text-white shadow-2xs' : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>calibration.json</span>
              <span
                v-if="calibrationCount !== null"
                class="px-1.5 py-0.2 rounded-full text-[10px] font-mono"
                :class="activeFile === 'calibration' ? 'bg-purple-700/60 text-white' : 'bg-gray-100 text-gray-600'"
              >
                {{ calibrationCount }}
              </span>
            </button>
          </div>

          <!-- View Mode & Search Filter -->
          <div class="flex items-center gap-2.5 flex-wrap">
            <!-- Search Filter (hidden in raw view) -->
            <div v-if="viewMode !== 'raw'" class="relative min-w-[200px] sm:min-w-[260px]">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Filter keys, values, or qubits..."
                class="w-full pl-8 pr-7 py-1.5 text-xs bg-gray-100/90 hover:bg-gray-100 focus:bg-white rounded-xl border-0 focus:outline-none focus:ring-2 focus:ring-purple-400/50 shadow-inner transition text-gray-800 placeholder-gray-400"
              />
              <svg class="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <button
                v-if="searchQuery"
                @click="searchQuery = ''"
                class="text-gray-400 hover:text-gray-600 absolute right-2.5 top-2 cursor-pointer font-bold text-xs"
              >
                &times;
              </button>
            </div>

            <!-- View Modes: Boxes / Pulses (if parameters) / Graph / Raw -->
            <div class="inline-flex p-0.5 bg-gray-200/70 rounded-xl shadow-inner text-xs font-semibold">
              <button
                type="button"
                @click="viewMode = 'boxes'"
                class="px-2.5 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1"
                :class="viewMode === 'boxes' ? 'bg-white text-[#833dff] shadow-xs' : 'text-gray-600 hover:text-gray-900'"
                title="Hierarchical collapsible boxes view"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
                <span>Boxes</span>
              </button>
              <button
                v-if="activeFile === 'parameters'"
                type="button"
                @click="viewMode = 'pulses'"
                class="px-2.5 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1"
                :class="viewMode === 'pulses' ? 'bg-white text-[#833dff] shadow-xs' : 'text-gray-600 hover:text-gray-900'"
                title="Multi-channel pulse sequence timelines for native gates"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Pulse Sequences</span>
              </button>
              <button
                type="button"
                @click="viewMode = 'graph'"
                class="px-2.5 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1"
                :class="viewMode === 'graph' ? 'bg-white text-[#833dff] shadow-xs' : 'text-gray-600 hover:text-gray-900'"
                title="Visual hierarchical graph view"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                </svg>
                <span>Graph</span>
              </button>
              <button
                type="button"
                @click="viewMode = 'raw'"
                class="px-2.5 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1"
                :class="viewMode === 'raw' ? 'bg-white text-[#833dff] shadow-xs' : 'text-gray-600 hover:text-gray-900'"
                title="Raw JSON text"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                <span>Raw</span>
              </button>
            </div>

            <!-- Expand / Collapse All (for boxes mode) -->
            <div v-if="viewMode === 'boxes'" class="flex items-center gap-1">
              <button
                type="button"
                @click="expandAllState = true"
                class="px-2 py-1 rounded-lg bg-white hover:bg-gray-50 border border-gray-200 text-[11px] font-medium text-gray-600 transition cursor-pointer"
                title="Expand all branches"
              >
                Expand All
              </button>
              <button
                type="button"
                @click="expandAllState = false"
                class="px-2 py-1 rounded-lg bg-white hover:bg-gray-50 border border-gray-200 text-[11px] font-medium text-gray-600 transition cursor-pointer"
                title="Collapse all branches"
              >
                Collapse
              </button>
            </div>

            <!-- Copy JSON -->
            <button
              type="button"
              @click="handleCopyActiveJson"
              class="px-2.5 py-1 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs text-xs font-semibold inline-flex items-center gap-1 transition cursor-pointer"
              title="Copy active JSON to clipboard"
            >
              <svg class="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <span>{{ copyStatusText }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Main Body / View Rendering Area -->
      <div class="p-4 sm:p-6 flex-1">
        <!-- Loading State -->
        <div v-if="loading" class="flex flex-col items-center justify-center h-64">
          <loading-spinner label="Loading platform data..." />
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="bg-red-50 text-red-700 p-6 rounded-2xl border border-red-200 max-w-2xl mx-auto my-8">
          <h3 class="font-bold text-base">Unable to load platform data</h3>
          <p class="text-xs mt-1">{{ error }}</p>
          <div class="flex items-center gap-2 mt-4">
            <button
              type="button"
              @click="goBackToReport"
              class="px-3 py-1.5 bg-red-100 text-red-800 rounded-lg text-xs font-semibold cursor-pointer hover:bg-red-200 transition"
            >
              Back to Report
            </button>
            <button
              type="button"
              @click="loadPlatformData"
              class="px-3 py-1.5 bg-white border border-red-200 text-red-700 rounded-lg text-xs font-semibold hover:bg-red-50 transition cursor-pointer"
            >
              Retry
            </button>
          </div>
        </div>

        <!-- Empty File State -->
        <div v-else-if="!activeFileData" class="bg-amber-50 text-amber-800 p-6 rounded-2xl border border-amber-200 max-w-2xl mx-auto my-8 text-center">
          <h3 class="font-bold text-base">No {{ activeFile }}.json found</h3>
          <p class="text-xs mt-1 text-amber-700">
            This report does not have a valid {{ activeFile }}.json in its {{ activePlatformType }} platform folder.
          </p>
        </div>

        <!-- Active View Display -->
        <div v-else class="max-w-7xl mx-auto space-y-4">
          <!-- 1. Hierarchical Boxes View -->
          <div v-if="viewMode === 'boxes'" class="space-y-4">
            <template v-if="filteredTree?.branchEntries?.length || filteredTree?.leafEntries?.length">
              <!-- Top-level Leaf Properties if any -->
              <div v-if="filteredTree.leafEntries?.length > 0" class="p-4 bg-white rounded-xl border border-gray-200 shadow-2xs">
                <h4 class="text-xs font-bold font-mono text-gray-500 uppercase tracking-wider mb-2.5">
                  Root Properties
                </h4>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2.5">
                  <platform-leaf-property
                    v-for="leaf in filteredTree.leafEntries"
                    :key="leaf.path"
                    :leaf="leaf"
                  />
                </div>
              </div>

              <!-- Top-level Branches -->
              <div class="space-y-4">
                <platform-box-node
                  v-for="branch in filteredTree.branchEntries"
                  :key="branch.id"
                  :node="branch"
                  :expand-all="expandAllState"
                />
              </div>
            </template>

            <!-- No search matches -->
            <div v-else class="text-center py-12 bg-white rounded-xl border border-gray-200 text-gray-400 text-xs">
              No properties or branches matching "<span class="font-mono text-gray-700">{{ searchQuery }}</span>"
            </div>
          </div>

          <!-- 2. Pulse Sequences Dedicated View -->
          <div v-else-if="viewMode === 'pulses'" class="space-y-6">
            <div class="flex items-center justify-between gap-3 p-4 bg-purple-50/50 rounded-2xl border border-purple-100 flex-wrap">
              <div>
                <h3 class="font-bold text-gray-900 text-sm">Native Gate Pulse Sequences</h3>
                <p class="text-xs text-gray-500 mt-0.5">
                  Synchronized multi-channel pulse-like events across control channels (drive, flux, acquisition)
                </p>
              </div>

              <!-- Filter by Category -->
              <div class="flex items-center gap-1.5 flex-wrap">
                <button
                  type="button"
                  @click="pulseCategoryFilter = 'all'"
                  class="px-2.5 py-1 rounded-lg text-xs font-semibold transition cursor-pointer"
                  :class="pulseCategoryFilter === 'all' ? 'bg-[#833dff] text-white shadow-xs' : 'bg-white text-gray-700 hover:bg-purple-50 border border-gray-200'"
                >
                  All Gates ({{ allNativeGates.length }})
                </button>
                <button
                  type="button"
                  @click="pulseCategoryFilter = 'single_qubit'"
                  class="px-2.5 py-1 rounded-lg text-xs font-semibold transition cursor-pointer"
                  :class="pulseCategoryFilter === 'single_qubit' ? 'bg-[#833dff] text-white shadow-xs' : 'bg-white text-gray-700 hover:bg-purple-50 border border-gray-200'"
                >
                  Single Qubit
                </button>
                <button
                  type="button"
                  @click="pulseCategoryFilter = 'two_qubit'"
                  class="px-2.5 py-1 rounded-lg text-xs font-semibold transition cursor-pointer"
                  :class="pulseCategoryFilter === 'two_qubit' ? 'bg-[#833dff] text-white shadow-xs' : 'bg-white text-gray-700 hover:bg-purple-50 border border-gray-200'"
                >
                  Two Qubit
                </button>
              </div>
            </div>

            <!-- List of Native Gates with Pulse Diagrams -->
            <div v-if="filteredNativeGates.length > 0" class="space-y-6">
              <div
                v-for="gate in filteredNativeGates"
                :key="gate.id"
                class="space-y-2"
              >
                <div class="flex items-center gap-2 pl-1">
                  <span class="text-xs font-bold font-mono px-2 py-0.5 rounded bg-gray-200/80 text-gray-800">
                    {{ gate.targetLabel }}
                  </span>
                  <span class="text-xs font-semibold text-purple-700 font-mono">
                    {{ gate.category }}
                  </span>
                </div>
                <platform-pulse-sequence
                  :sequence="gate.sequence"
                  :gate-name="gate.name"
                />
              </div>
            </div>

            <div v-else class="text-center py-12 bg-white rounded-2xl border border-gray-200 text-gray-400 text-xs">
              No calibrated native gates found matching the criteria.
            </div>
          </div>

          <!-- 3. Hierarchy Tree Graph View -->
          <div v-else-if="viewMode === 'graph'">
            <platform-graph-view
              v-if="filteredTree"
              :root-node="filteredTree"
            />
          </div>

          <!-- 4. Raw JSON View -->
          <div v-else-if="viewMode === 'raw'" class="relative">
            <div class="p-4 bg-gray-900 text-purple-100 rounded-2xl font-mono text-xs overflow-x-auto shadow-inner max-h-[700px]">
              <pre>{{ formattedJsonString }}</pre>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import Sidebar from '../components/Sidebar.vue'
import PlatformBoxNode from '../components/platform/PlatformBoxNode.vue'
import PlatformLeafProperty from '../components/platform/PlatformLeafProperty.vue'
import PlatformGraphView from '../components/platform/PlatformGraphView.vue'
import PlatformPulseSequence from '../components/platform/PlatformPulseSequence.vue'
import { getApiUrl } from '../store.js'
import { buildTreeNode, filterTree, isPulseSequence } from '../utils/platformTree.js'
import { copyToClipboard } from '../utils/clipboard.js'

const route = useRoute()
const router = useRouter()

const reportId = computed(() => {
  return route.params.id || ''
})

const activePlatformType = ref(route.query.type === 'old' ? 'old' : 'new')
const activeFile = ref('calibration') // 'calibration' or 'parameters'
const viewMode = ref('boxes') // 'boxes', 'graph', 'raw'
const searchQuery = ref('')
const expandAllState = ref(null)
const copyStatusText = ref('Copy JSON')

const loading = ref(true)
const error = ref(null)
const platformData = ref(null)

const downloadZipUrl = computed(() => {
  const encId = encodeURIComponent(reportId.value)
  const endpoint = activePlatformType.value === 'old' ? 'download/old-platform' : 'download/new-platform'
  return getApiUrl(`/api/reports/${encId}/${endpoint}`)
})

async function loadPlatformData() {
  loading.value = true
  error.value = null
  try {
    const encId = encodeURIComponent(reportId.value)
    const url = getApiUrl(`/api/reports/${encId}/platform/${activePlatformType.value}`)
    const res = await fetch(url)
    if (!res.ok) {
      throw new Error(`Failed to load platform data (${res.status} ${res.statusText})`)
    }
    platformData.value = await res.json()
  } catch (err) {
    console.error('Error fetching platform data:', err)
    error.value = err.message || 'Error loading platform data'
  } finally {
    loading.value = false
  }
}

function switchPlatformType(type) {
  if (activePlatformType.value === type) return
  activePlatformType.value = type
  router.replace({
    query: {
      ...route.query,
      type
    }
  })
  loadPlatformData()
}

function goBackToReport() {
  router.push({
    name: 'report',
    params: { id: reportId.value }
  })
}

const activeFileData = computed(() => {
  if (!platformData.value) return null
  return activeFile.value === 'parameters'
    ? platformData.value.parameters
    : platformData.value.calibration
})

const parametersCount = computed(() => {
  const p = platformData.value?.parameters
  return p && typeof p === 'object' ? Object.keys(p).length : null
})

const calibrationCount = computed(() => {
  const c = platformData.value?.calibration
  return c && typeof c === 'object' ? Object.keys(c).length : null
})

const rawTree = computed(() => {
  if (!activeFileData.value) return null
  return buildTreeNode('root', activeFileData.value)
})

const filteredTree = computed(() => {
  if (!rawTree.value) return null
  if (!searchQuery.value) return rawTree.value
  const result = filterTree(rawTree.value, searchQuery.value)
  return result.node
})

const formattedJsonString = computed(() => {
  if (!activeFileData.value) return ''
  return JSON.stringify(activeFileData.value, null, 2)
})

function handleCopyActiveJson() {
  if (!formattedJsonString.value) return
  copyToClipboard(formattedJsonString.value)
  copyStatusText.value = 'Copied!'
  setTimeout(() => {
    copyStatusText.value = 'Copy JSON'
  }, 1200)
}

// Native Gate Pulse Sequences logic
const pulseCategoryFilter = ref('all')

const allNativeGates = computed(() => {
  const ng = platformData.value?.parameters?.native_gates
  if (!ng || typeof ng !== 'object') return []

  const gates = []
  Object.entries(ng).forEach(([category, targets]) => {
    if (!targets || typeof targets !== 'object') return
    Object.entries(targets).forEach(([target, gateDict]) => {
      if (!gateDict || typeof gateDict !== 'object') return
      Object.entries(gateDict).forEach(([gateName, seq]) => {
        if (isPulseSequence(seq)) {
          const targetLabel = category === 'single_qubit' ? `Qubit ${target}` : `Qubits ${target}`
          gates.push({
            id: `${category}-${target}-${gateName}`,
            category,
            target,
            targetLabel,
            name: `${targetLabel} : ${gateName}`,
            gateName,
            sequence: seq
          })
        }
      })
    })
  })
  return gates
})

const filteredNativeGates = computed(() => {
  let list = allNativeGates.value
  if (pulseCategoryFilter.value !== 'all') {
    list = list.filter(g => g.category === pulseCategoryFilter.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter(g => {
      return (
        g.name.toLowerCase().includes(q) ||
        g.gateName.toLowerCase().includes(q) ||
        g.target.toLowerCase().includes(q) ||
        JSON.stringify(g.sequence).toLowerCase().includes(q)
      )
    })
  }
  return list
})

watch(activeFile, (newFile) => {
  if (newFile === 'calibration' && viewMode.value === 'pulses') {
    viewMode.value = 'boxes'
  }
})

watch(() => route.params.id, () => {
  loadPlatformData()
})

onMounted(() => {
  loadPlatformData()
})
</script>

<style scoped>
</style>
