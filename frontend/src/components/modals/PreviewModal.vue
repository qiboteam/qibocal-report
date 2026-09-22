<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-2xl max-w-5xl w-full p-6 shadow-2xl border border-gray-100 flex flex-col max-h-[90vh]">
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
        <button
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-700 p-1.5 rounded-lg hover:bg-gray-100 text-lg transition cursor-pointer shrink-0"
        >
          &times;
        </button>
      </div>

      <!-- Body: plots-only preview -->
      <div class="flex-1 min-h-0 overflow-y-auto mt-4">
        <div v-if="loading" class="flex flex-col items-center justify-center h-64">
          <loading-spinner label="Loading preview..." />
        </div>

        <div v-else-if="error" class="p-8 text-center text-xs text-red-600">
          Failed to load preview: {{ error }}
        </div>

        <div v-else-if="protocolGroups.length === 0" class="p-12 text-center text-xs text-gray-400">
          No figures available to preview for this report.
        </div>

        <div v-else class="space-y-6">
          <div v-for="group in protocolGroups" :key="group.id || group.name">
            <h3 class="text-sm font-bold text-gray-900 mb-2">
              <span class="px-2.5 py-0.5 rounded-lg bg-purple-50 text-purple-700 inline-block">
                {{ extractProtocolType(group.name) }}
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
import { ref, watch } from 'vue'
import { apiFetch } from '../../store.js'
import LoadingSpinner from '../LoadingSpinner.vue'
import PlotlyViewer from '../PlotlyViewer.vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  report: { type: Object, default: null }
})

defineEmits(['close'])

const loading = ref(false)
const error = ref(null)
const protocolGroups = ref([])

function extractProtocolType(name) {
  return name.replace(/-\d+$/, '')
}

async function loadPreview() {
  if (!props.report?.id) return
  loading.value = true
  error.value = null
  protocolGroups.value = []
  try {
    const encodedId = encodeURIComponent(props.report.id)
    const res = await apiFetch(`/api/reports/${encodedId}/protocols`)
    if (!res.ok) {
      throw new Error(`Failed to load protocols (${res.status})`)
    }
    const protocols = await res.json()
    protocolGroups.value = (protocols || [])
      .filter(proto => proto.figures && proto.figures.length > 0)
      .map(proto => ({
        id: proto.id,
        name: proto.name || proto.id,
        figures: proto.figures
      }))
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.show, props.report?.id],
  ([show, id]) => {
    if (show && id) {
      loadPreview()
    } else {
      protocolGroups.value = []
    }
  }
)
</script>
