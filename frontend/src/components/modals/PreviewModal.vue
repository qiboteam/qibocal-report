<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
    style="bottom: var(--diagnostics-height, 0px)"
    @click.self="close"
  >
    <div class="bg-white rounded-2xl max-w-5xl w-full p-6 shadow-2xl border border-gray-100 flex flex-col" style="max-height: calc(var(--app-height, 100vh) * 0.9)">
      <!-- Header -->
      <div class="flex items-center justify-between pb-4 border-b border-gray-100 shrink-0">
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="w-9 h-9 rounded-xl bg-purple-50 text-[#833dff] flex items-center justify-center font-bold shrink-0">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>
          <h2 class="text-base font-bold text-gray-900 leading-tight truncate">
            {{ report?.id || 'Preview' }}
          </h2>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            @click="close"
            aria-label="Close preview"
            class="text-gray-400 hover:text-gray-700 p-1.5 rounded-lg hover:bg-gray-100 text-lg transition cursor-pointer shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            &times;
          </button>
        </div>
      </div>

      <!-- Body: plots-only preview -->
      <div class="flex-1 min-h-0 overflow-y-auto mt-4">
        <div v-if="loading" class="flex flex-col items-center justify-center h-64">
          <loading-spinner label="Loading preview..." />
        </div>

        <div v-else-if="error" class="p-8 text-center text-xs text-red-600">
          Failed to load preview: {{ error }}
        </div>

        <div v-else class="space-y-6">
          <plot-generation-errors :protocols="protocols" />
          <div v-if="protocolGroups.length === 0 && !generationErrors.length" class="p-12 text-center text-xs text-gray-400">
            No figures available to preview for this report.
          </div>
          <div v-for="group in protocolGroups" :key="group.id || group.name">
            <h3 class="text-sm font-bold text-gray-900 mb-2">
              <span class="px-2.5 py-0.5 rounded-lg bg-purple-50 text-purple-700 inline-block">
                {{ extractProtocolType(group.name || group.id) }}
              </span>
            </h3>
            <div class="space-y-4">
              <plotly-viewer
                v-for="fig in group.figures"
                :key="fig.id || fig.title"
                :figure="fig"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { state } from '../../store.js'
import { apiFetch } from '../../api.js'
import { getPlotGenerationErrors } from '../../utils/plotGeneration.js'
import { diagnostics } from '../../composables/useDiagnostics.js'
import LoadingSpinner from '../LoadingSpinner.vue'
import PlotlyViewer from '../PlotlyViewer.vue'
import PlotGenerationErrors from '../report/PlotGenerationErrors.vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  report: { type: Object, default: null }
})

const emit = defineEmits(['close'])

const loading = ref(false)
const error = ref(null)
const protocols = ref([])
const protocolGroups = computed(() => protocols.value.filter(proto => proto.figures?.length))
const generationErrors = computed(() => getPlotGenerationErrors(protocols.value))
let requestVersion = 0

function close() {
  emit('close')
}

function extractProtocolType(name = '') {
  return name.replace(/-\d+$/, '')
}

async function loadPreview(regenerate = false) {
  if (!props.show || !props.report?.id) return
  const version = ++requestVersion
  const server = state.activeServer
  loading.value = true
  error.value = null
  protocols.value = []
  try {
    const encodedId = encodeURIComponent(props.report.id)
    const res = await apiFetch(
      `/api/reports/${encodedId}/${regenerate ? 'regenerate' : 'protocols'}`,
      regenerate ? { method: 'POST' } : {},
      server
    )
    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || `Failed to load protocols (${res.status})`)
    }
    const data = await res.json()
    if (version === requestVersion) protocols.value = data
  } catch (err) {
    if (version === requestVersion) error.value = err.message
  } finally {
    if (version === requestVersion) loading.value = false
  }
}

watch(
  () => [props.show, props.report?.id, state.activeServer?.id, state.activeServer?.url],
  ([show, id]) => {
    if (show && id) {
      loadPreview()
    } else {
      requestVersion++
      protocols.value = []
    }
  },
  { immediate: true }
)

watch(() => diagnostics.qibocalRevision, () => {
  if (props.show) loadPreview(true)
})

onUnmounted(() => { requestVersion++ })
</script>
