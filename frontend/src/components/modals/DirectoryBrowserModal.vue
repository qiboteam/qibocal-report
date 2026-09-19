<template>
  <div
    v-if="show"
    class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-2xl max-w-lg w-full p-5 shadow-2xl border border-black/[0.08] flex flex-col max-h-[85vh] overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between pb-3 border-b border-gray-100 shrink-0">
        <div class="flex items-center gap-2 text-gray-900 font-bold text-sm">
          <svg class="w-4 h-4 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          {{ filterMode ? 'Filter by Folder' : 'Select Report Directory' }}
        </div>
        <button
          type="button"
          @click="$emit('close')"
          class="border-0 w-6 h-6 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition cursor-pointer"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Navigation & Breadcrumbs Bar -->
      <div class="mt-3.5 flex items-center gap-1.5 p-1.5 bg-gray-50/90 rounded-xl border border-gray-200/80 shrink-0 text-xs">
        <button
          type="button"
          :disabled="parentPath === null || loading"
          @click="browseTo(parentPath)"
          class="p-1 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 text-gray-600 disabled:opacity-40 disabled:pointer-events-none transition cursor-pointer shrink-0"
          title="Go to parent folder"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <!-- Breadcrumbs -->
        <div class="flex items-center gap-1 overflow-x-auto min-w-0 flex-1 py-0.5 no-scrollbar">
          <template v-for="(crumb, idx) in breadcrumbs" :key="crumb.path || 'root'">
            <span v-if="idx > 0" class="text-gray-300 shrink-0 select-none">/</span>
            <button
              type="button"
              @click="browseTo(crumb.path)"
              class="px-1.5 py-0.5 rounded text-[11px] font-medium truncate max-w-[120px] transition border-0 bg-transparent cursor-pointer"
              :class="idx === breadcrumbs.length - 1
                ? 'font-bold text-[#833dff] bg-purple-50'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/60'"
              :title="crumb.name"
            >
              {{ crumb.name }}
            </button>
          </template>
        </div>

        <button
          type="button"
          :disabled="loading"
          @click="browseTo(currentBrowsePath)"
          class="p-1 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 text-gray-500 hover:text-gray-800 disabled:opacity-40 transition cursor-pointer shrink-0"
          title="Refresh folder"
        >
          <svg class="w-3.5 h-3.5" :class="loading ? 'animate-spin' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      <!-- Current Location Quick Selection Card -->
      <div
        class="mt-2.5 p-2.5 rounded-xl border transition flex items-center justify-between shrink-0 cursor-pointer"
        :class="selectedPath === currentBrowsePath
          ? 'bg-purple-50/70 border-purple-300 ring-1 ring-[#833dff]/30'
          : 'bg-white border-gray-200 hover:border-purple-200'"
        @click="selectedPath = currentBrowsePath"
      >
        <div class="flex items-center gap-2 min-w-0">
          <svg class="w-4 h-4 text-[#833dff] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <div class="min-w-0">
            <div class="flex items-center gap-1.5">
              <span class="text-xs font-semibold text-gray-800 truncate">
                {{ currentBrowsePath ? currentBrowsePath.split('/').pop() : (filterMode ? 'All Folders (Root)' : 'Root Directory') }}
              </span>
              <span v-if="isActiveRoot" class="px-1.5 py-0.2 text-[9px] font-bold bg-emerald-100 text-emerald-800 rounded font-mono">
                {{ filterMode ? 'Server Root' : 'Active Server Root' }}
              </span>
              <span v-if="reportsCount > 0" class="px-1.5 py-0.2 text-[9px] font-mono font-medium bg-purple-100 text-purple-800 rounded">
                {{ reportsCount }} {{ reportsCount === 1 ? 'report' : 'reports' }}
              </span>
            </div>
            <p class="text-[10px] text-gray-400 font-mono truncate mt-0.5">
              {{ currentBrowsePath || '/' }}
            </p>
          </div>
        </div>

        <button
          type="button"
          @click.stop="selectedPath = currentBrowsePath"
          class="border-0 px-2.5 py-1 rounded-lg text-[11px] font-medium transition cursor-pointer shrink-0"
          :class="selectedPath === currentBrowsePath
            ? 'bg-[#833dff] text-white shadow-2xs font-semibold'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          {{ selectedPath === currentBrowsePath ? 'Selected' : (filterMode ? 'Select This Folder' : 'Select Folder') }}
        </button>
      </div>

      <!-- Subdirectories Header -->
      <div class="mt-3 mb-1 px-1 flex items-center justify-between shrink-0">
        <span class="text-[11px] font-bold uppercase tracking-wider text-gray-500">
          Subfolders ({{ directories.length }})
        </span>
        <span v-if="directories.length > 0" class="text-[10px] text-gray-400">
          Click row to select, or arrow to enter
        </span>
      </div>

      <!-- Subdirectories List -->
      <div class="flex-1 min-h-[140px] max-h-56 overflow-y-auto pr-1 space-y-1">
        <div v-if="loading" class="flex flex-col items-center justify-center h-28 text-gray-400 text-xs">
          <div class="w-5 h-5 border-2 border-[#833dff] border-t-transparent rounded-full animate-spin"></div>
          <span class="mt-2 text-[11px]">Loading folders...</span>
        </div>

        <div v-else-if="error" class="p-3 bg-red-50 text-red-700 text-xs rounded-xl border border-red-200">
          {{ error }}
        </div>

        <div v-else-if="directories.length === 0" class="p-4 text-center text-[11px] text-gray-400 italic bg-gray-50/60 rounded-xl border border-dashed border-gray-200">
          <span v-if="reportsCount > 0">
            No further subfolders. This folder contains {{ reportsCount }} calibration {{ reportsCount === 1 ? 'report' : 'reports' }}.
          </span>
          <span v-else>
            No subdirectories inside this folder.
          </span>
        </div>

        <div
          v-else
          v-for="dir in directories"
          :key="dir.path"
          @click="selectedPath = dir.path"
          class="p-2 rounded-xl border transition flex items-center justify-between gap-2 cursor-pointer group"
          :class="selectedPath === dir.path
            ? 'bg-purple-50/70 border-purple-300 ring-1 ring-[#833dff]/20'
            : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300'"
        >
          <div class="flex items-center gap-2 min-w-0">
            <svg class="w-4 h-4 text-gray-400 group-hover:text-[#833dff] shrink-0 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            <div class="min-w-0">
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-medium text-gray-900 truncate" :title="dir.name">{{ dir.name }}</span>
                <span v-if="dir.is_current" class="px-1.5 py-0.2 text-[9px] font-bold bg-emerald-100 text-emerald-800 rounded font-mono">
                  Active
                </span>
                <span v-if="dir.reports_count > 0" class="px-1.5 py-0.2 text-[9px] font-mono font-medium bg-purple-100 text-purple-800 rounded">
                  {{ dir.reports_count }} {{ dir.reports_count === 1 ? 'report' : 'reports' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Actions on item: Enter Subfolder (Arrow only) -->
          <div class="flex items-center gap-1 shrink-0">
            <button
              v-if="dir.has_subdirs"
              type="button"
              @click.stop="browseTo(dir.path)"
              class="w-7 h-7 flex items-center justify-center bg-gray-100 hover:bg-purple-100 hover:text-[#833dff] text-gray-600 rounded-lg transition cursor-pointer"
              title="Open folder"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Action Footer -->
      <div class="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between gap-3 shrink-0">
        <div class="min-w-0">
          <span class="text-[10px] text-gray-400 uppercase tracking-wider block">Target Selection</span>
          <span class="text-xs font-mono font-semibold text-gray-800 truncate block max-w-[220px]" :title="selectedPath || (filterMode ? 'All folders (no filter)' : '(Root directory)')">
            📁 {{ selectedPath || (filterMode ? 'All folders (no filter)' : '(Root directory)') }}
          </span>
        </div>

        <div class="flex items-center gap-2 shrink-0">
          <button
            v-if="filterMode && selectedPath"
            type="button"
            @click="selectedPath = ''"
            class="border-0 px-2.5 py-1.5 rounded-lg text-xs font-medium text-purple-700 hover:bg-purple-50 transition cursor-pointer"
          >
            Clear Filter
          </button>
          <button
            type="button"
            @click="$emit('close')"
            class="border-0 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-100 transition cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            :disabled="applying || loading"
            @click="applyChange"
            class="border-0 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-[#833dff] text-white hover:bg-[#722ce6] active:scale-[0.98] transition shadow-2xs disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
          >
            <svg v-if="applying" class="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {{ applying ? 'Applying...' : (filterMode ? 'Apply Filter' : 'Apply Selection') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { normalizeUrl } from '../../store.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  serverUrl: { type: String, default: '' },
  initialPath: { type: String, default: '' },
  filterMode: { type: Boolean, default: false }
})

const emit = defineEmits(['close', 'select'])

const loading = ref(false)
const applying = ref(false)
const error = ref(null)

const originalRoot = ref('')
const currentRoot = ref('')
const currentBrowsePath = ref('')
const parentPath = ref(null)
const breadcrumbs = ref([])
const directories = ref([])
const isActiveRoot = ref(false)
const reportsCount = ref(0)
const selectedPath = ref('')

watch(
  () => props.show,
  (val) => {
    if (val) {
      selectedPath.value = props.initialPath || ''
      browseTo(props.initialPath || '')
    }
  }
)

async function browseTo(subpath = '') {
  loading.value = true
  error.value = null
  try {
    const base = normalizeUrl(props.serverUrl)
    const url = new URL(`${base || ''}/api/server/directory/browse`, window.location.origin)
    if (subpath) {
      url.searchParams.set('path', subpath)
    }
    if (props.filterMode) {
      url.searchParams.set('scope', 'root')
    }
    const res = await fetch(url.toString(), { signal: AbortSignal.timeout(6000) })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Failed to browse directory (${res.status})`)
    }
    const data = await res.json()
    originalRoot.value = data.original_root
    currentRoot.value = data.current_root
    currentBrowsePath.value = data.current_browse_path
    parentPath.value = data.parent_path
    breadcrumbs.value = data.breadcrumbs || []
    directories.value = data.directories || []
    isActiveRoot.value = data.is_active_root
    reportsCount.value = data.reports_count || 0
    if (selectedPath.value === '') {
      selectedPath.value = data.current_browse_path
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function applyChange() {
  if (props.filterMode) {
    emit('select', { path: selectedPath.value })
    emit('close')
    return
  }
  applying.value = true
  error.value = null
  try {
    const base = normalizeUrl(props.serverUrl)
    const targetUrl = `${base || ''}/api/server/directory`
    const res = await fetch(targetUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: selectedPath.value })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Failed to change directory (${res.status})`)
    }
    const dirInfo = await res.json()
    emit('select', { path: selectedPath.value, dirInfo })
    emit('close')
  } catch (err) {
    error.value = err.message
  } finally {
    applying.value = false
  }
}

onMounted(() => {
  if (props.show) {
    browseTo(props.initialPath || '')
  }
})
</script>
