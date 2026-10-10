<template>
  <div v-if="!isCollapsed">
    <!-- Download & Meta Actions Row -->
    <div class="mb-2.5 pb-2.5 border-b border-gray-100">
      <div class="flex items-center justify-evenly gap-1.5 w-full">
        <!-- Download Full Protocol Folder (.zip) -->
        <api-file-button
          :path="downloadFullPath"
          :filename="getReportDownloadFilename(reportId)"
          class="flex-1 max-w-[52px] h-7 rounded-lg bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer shrink-0"
          title="Download full protocol folder (.zip)"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </api-file-button>

        <button
          type="button"
          @click="copyReportPath"
          :disabled="copyingPath || !reportId"
          :aria-busy="copyingPath"
          :title="pathCopyTitle"
          :aria-label="pathCopyTitle"
          class="flex-1 max-w-[52px] h-7 rounded-lg bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer shrink-0 disabled:opacity-50"
        >
          <Check v-if="pathCopied" class="w-3.5 h-3.5 text-emerald-600" />
          <Copy v-else class="w-3.5 h-3.5" />
        </button>

        <!-- Download New Platform (.zip) -->
        <api-file-button
          :path="downloadNewPlatformPath"
          :filename="getReportDownloadFilename(reportId, '_new_platform')"
          class="group flex-1 max-w-[52px] h-7 rounded-lg bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer shrink-0"
          title="Download new platform (.zip)"
        >
          <svg class="h-3.5 w-auto shrink-0" viewBox="0 0 26 24" fill="none">
            <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M3 9h2m-2 6h2m14-6h2m-2 6h2M7 5h10a2 2 0 012 2v10a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2z" />
            <path d="M15 3.5C15 6 13 8.5 10 8.5C13 8.5 15 11 15 13.5C15 11 17 8.5 20 8.5C17 8.5 15 6 15 3.5Z" class="fill-gray-400 group-hover:fill-[#833dff] transition-colors" />
            <path d="M22 0.5C22 2 20.5 3.5 19 3.5C20.5 3.5 22 5 22 6.5C22 5 23.5 3.5 25 3.5C23.5 3.5 22 2 22 0.5Z" class="fill-gray-400 group-hover:fill-[#833dff] transition-colors" />
          </svg>
        </api-file-button>

        <!-- Download Old Platform (.zip) -->
        <api-file-button
          :path="downloadOldPlatformPath"
          :filename="getReportDownloadFilename(reportId, '_old_platform')"
          class="flex-1 max-w-[52px] h-7 rounded-lg bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer shrink-0"
          title="Download old platform (.zip)"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M3 9h2m-2 6h2m14-6h2m-2 6h2M7 5h10a2 2 0 012 2v10a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2z" />
          </svg>
        </api-file-button>

        <!-- View meta.json (plain JSON in new browser tab) -->
        <api-file-button
          :path="metaJsonPath"
          preview
          class="flex-1 max-w-[52px] h-7 rounded-lg bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer shrink-0 font-mono font-bold text-xs no-underline"
          style="text-decoration: none;"
          title="View meta.json (plain JSON)"
        >
          { }
        </api-file-button>
      </div>
    </div>

    <!-- Expanded Protocol Summary -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-bold uppercase tracking-wider text-gray-800">Protocols Summary</span>
      <span class="text-[11px] text-purple-700 font-mono bg-purple-100 px-1.5 py-0.5 rounded">
        {{ protocols?.length || 0 }} routines
      </span>
    </div>

    <div class="space-y-1.5">
      <button
        type="button"
        @click="$emit('select-protocol', null)"
        :aria-current="activeSlide === null ? 'page' : undefined"
        class="w-full text-left block p-2 rounded-xl text-xs font-semibold hover:bg-purple-50 border border-gray-100 cursor-pointer"
        :class="activeSlide === null ? 'bg-purple-100 text-purple-800' : 'text-gray-800'"
      >
        Report Overview
      </button>
      <a
        v-for="p in protocols"
        :key="p.id"
        :href="`#proto-${p.id}`"
        @click.prevent="$emit('select-protocol', p.id)"
        :aria-current="activeSlide === p.id ? 'page' : undefined"
        :class="activeSlide === p.id ? 'bg-purple-100 border-purple-200' : ''"
        class="block p-2 rounded-xl text-xs hover:bg-purple-50/70 border border-gray-100 hover:border-purple-200 transition group cursor-pointer"
      >
        <div class="flex items-center justify-between">
          <span class="font-semibold text-gray-800 group-hover:text-[#833dff] truncate">{{ p.name }}</span>
          <div class="flex items-center gap-1.5 shrink-0 ml-1.5">
            <a
              v-if="getDocLink(p)"
              :href="getDocLink(p)"
              target="_blank"
              rel="noopener noreferrer"
              @click.stop
              class="text-gray-400 hover:text-[#833dff] transition-colors p-1 rounded hover:bg-white inline-flex items-center"
              :title="`Open documentation for ${p.name}`"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
            <span class="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 rounded">✓</span>
          </div>
        </div>
        <div class="flex items-center justify-between text-[10px] text-gray-400 mt-1 font-mono">
          <span>{{ p.execution_time || 'N/A' }}</span>
          <span>{{ p.num_figures || (p.figures ? p.figures.length : 0) }} plots</span>
        </div>
      </a>
    </div>
  </div>

  <div v-else class="flex flex-col items-center gap-1.5 w-full">
    <!-- Collapsed Quick Actions for Report Page -->
    <button
      @click="$emit('print-pdf')"
      class="w-9 h-9 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer"
      title="Print to PDF"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
      </svg>
    </button>

    <button
      @click="!isViewer && $emit('regenerate')"
      :disabled="regenerating || isViewer"
      class="w-9 h-9 rounded-xl bg-white text-gray-700 border border-gray-200 shadow-2xs flex items-center justify-center transition"
      :class="isViewer ? 'opacity-40 cursor-not-allowed' : 'hover:bg-purple-50 hover:text-[#833dff] hover:border-purple-300 disabled:opacity-50 cursor-pointer'"
      :title="isViewer ? 'Viewer role cannot regenerate plots' : 'Regenerate Plots'"
    >
      <svg
        class="w-4 h-4 text-[#833dff]"
        :class="regenerating ? 'animate-spin' : ''"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </button>

    <div class="w-6 border-b border-gray-200/80 my-1"></div>

    <!-- Collapsed Download & Meta Buttons -->
    <api-file-button
      :path="downloadFullPath"
      :filename="getReportDownloadFilename(reportId)"
      class="w-9 h-9 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer"
      title="Download full protocol folder (.zip)"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
    </api-file-button>

    <button
      type="button"
      @click="copyReportPath"
      :disabled="copyingPath || !reportId"
      :aria-busy="copyingPath"
      :title="pathCopyTitle"
      :aria-label="pathCopyTitle"
      class="w-9 h-9 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer disabled:opacity-50"
    >
      <Check v-if="pathCopied" class="w-4 h-4 text-emerald-600" />
      <Copy v-else class="w-4 h-4" />
    </button>

    <api-file-button
      :path="downloadNewPlatformPath"
      :filename="getReportDownloadFilename(reportId, '_new_platform')"
      class="group w-9 h-9 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer"
      title="Download new platform (.zip)"
    >
      <svg class="h-3.5 w-auto shrink-0" viewBox="0 0 26 24" fill="none">
        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M3 9h2m-2 6h2m14-6h2m-2 6h2M7 5h10a2 2 0 012 2v10a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2z" />
        <path d="M15 3.5C15 6 13 8.5 10 8.5C13 8.5 15 11 15 13.5C15 11 17 8.5 20 8.5C17 8.5 15 6 15 3.5Z" class="fill-gray-400 group-hover:fill-[#833dff] transition-colors" />
        <path d="M22 0.5C22 2 20.5 3.5 19 3.5C20.5 3.5 22 5 22 6.5C22 5 23.5 3.5 25 3.5C23.5 3.5 22 2 22 0.5Z" class="fill-gray-400 group-hover:fill-[#833dff] transition-colors" />
      </svg>
    </api-file-button>

    <api-file-button
      :path="downloadOldPlatformPath"
      :filename="getReportDownloadFilename(reportId, '_old_platform')"
      class="w-9 h-9 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer"
      title="Download old platform (.zip)"
    >
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M3 9h2m-2 6h2m14-6h2m-2 6h2M7 5h10a2 2 0 012 2v10a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2z" />
      </svg>
    </api-file-button>

    <api-file-button
      :path="metaJsonPath"
      preview
      class="w-9 h-9 rounded-xl bg-white hover:bg-purple-50 text-gray-700 hover:text-[#833dff] border border-gray-200 hover:border-purple-300 shadow-2xs flex items-center justify-center transition cursor-pointer font-mono font-bold text-xs no-underline"
      style="text-decoration: none;"
      title="View meta.json (plain JSON)"
    >
      { }
    </api-file-button>

    <div class="w-6 border-b border-gray-200/80 my-1"></div>

    <!-- Routine Count Badge -->
    <div
      v-if="protocols?.length"
      class="text-[10px] font-bold text-purple-700 bg-purple-100 px-1.5 py-0.5 rounded font-mono"
      :title="`Protocol Summary (${protocols.length} routines)`"
    >
      {{ protocols.length }}
    </div>

    <!-- Square Boxes with First Letters -->
    <button
      type="button"
      @click="$emit('select-protocol', null)"
      title="Report Overview"
      aria-label="Report Overview"
      :aria-current="activeSlide === null ? 'page' : undefined"
      class="w-9 h-9 rounded-xl flex items-center justify-center border border-purple-100 text-purple-800 hover:bg-purple-100 cursor-pointer shrink-0"
      :class="activeSlide === null ? 'bg-purple-100' : 'bg-purple-50'"
    >
      <LayoutDashboard class="w-4 h-4" />
    </button>
    <a
      v-for="p in protocols"
      :key="p.id"
      :href="`#proto-${p.id}`"
      @click.prevent="$emit('select-protocol', p.id)"
      :aria-current="activeSlide === p.id ? 'page' : undefined"
      class="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs font-mono transition cursor-pointer relative shadow-2xs group/proto shrink-0 select-none"
      :class="p.status === 'error'
        ? 'bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-500 hover:text-white'
        : 'bg-purple-50 text-purple-800 border border-purple-100 hover:bg-[#833dff] hover:text-white hover:border-[#833dff]'"
      :title="`${p.name} (${p.execution_time || 'N/A'}, ${p.num_figures || (p.figures ? p.figures.length : 0)} plots)`"
    >
      <span>{{ getInitial(p.name) }}</span>
      <span
        class="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full border border-white"
        :class="p.status === 'error' ? 'bg-amber-500' : 'bg-emerald-500'"
      ></span>
    </a>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Check, Copy, LayoutDashboard } from 'lucide-vue-next'
import { state, isViewer, getActiveAuthToken } from '../../store.js'
import { apiGetReportPath } from '../../api.js'
import { copyToClipboard } from '../../utils/clipboard.js'
import { getProtocolDocUrl } from '../../utils/protocolDocs.js'
import { getReportDownloadFilename } from '../../utils/apiFiles.js'
import ApiFileButton from '../ApiFileButton.vue'

const props = defineProps({
  protocols: { type: Array, default: () => [] },
  isCollapsed: { type: Boolean, default: false },
  regenerating: { type: Boolean, default: false },
  activeSlide: { type: String, default: undefined },
  reportId: { type: String, default: null }
})

defineEmits(['select-protocol', 'regenerate', 'print-pdf'])

const copyingPath = ref(false)
const pathCopied = ref(false)
const pathCopyTitle = computed(() => pathCopied.value
  ? 'Report path copied!'
  : 'Copy report folder path for qq upload')
let copyContext = 0

watch(
  () => [
    props.reportId, state.activeServer?.id, state.activeServer?.url,
    getActiveAuthToken(), state.auth.enabled, state.auth.user?.role
  ],
  () => {
    copyContext++
    pathCopied.value = false
  },
  { flush: 'sync' }
)

onBeforeUnmount(() => { copyContext++ })

async function copyReportPath() {
  if (copyingPath.value || !props.reportId) return
  copyingPath.value = true
  pathCopied.value = false
  const context = copyContext
  try {
    const response = await apiGetReportPath(props.reportId)
    if (context !== copyContext) return
    if (!response.ok) {
      throw new Error(`Failed to fetch report path (${response.status})`)
    }
    const data = await response.json()
    if (context !== copyContext) return
    if (!await copyToClipboard(data.path)) {
      throw new Error('Clipboard access failed')
    }
    if (context === copyContext) pathCopied.value = true
  } catch (err) {
    if (context === copyContext) window.alert(`Failed to copy report path: ${err.message}`)
  } finally {
    copyingPath.value = false
  }
}

function getDocLink(p) {
  return getProtocolDocUrl(p?.id, p?.name, state.activeServer)
}

const encodedId = computed(() => (props.reportId ? encodeURIComponent(props.reportId) : ''))

const downloadFullPath = computed(() => {
  if (!encodedId.value) return ''
  return `/api/reports/${encodedId.value}/download/full`
})

const downloadNewPlatformPath = computed(() => {
  if (!encodedId.value) return ''
  return `/api/reports/${encodedId.value}/download/new-platform`
})

const downloadOldPlatformPath = computed(() => {
  if (!encodedId.value) return ''
  return `/api/reports/${encodedId.value}/download/old-platform`
})

const metaJsonPath = computed(() => {
  if (!encodedId.value) return ''
  return `/api/reports/${encodedId.value}/meta.json`
})

function getInitial(name) {
  if (!name) return '?'
  const clean = name.replace(/^[^a-zA-Z0-9]+/, '')
  return (clean[0] || name[0] || '?').toUpperCase()
}

</script>
