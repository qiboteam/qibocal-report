<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between pb-3 border-b border-gray-100">
        <div class="flex items-center gap-2 text-gray-900 font-bold text-base">
          <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
          Archive Selected Reports
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 text-lg cursor-pointer">&times;</button>
      </div>

      <div class="mt-4 space-y-4">
        <p class="text-xs text-gray-500 leading-relaxed">
          Consolidate <strong class="text-gray-800">{{ selectedCount }}</strong> report(s) into a standalone archive in storage. You can inspect indexed reports anytime without unzipping, download the zip archive, or restore reports back to active status.
        </p>

        <!-- Archive Name -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1">Archive Name</label>
          <input
            v-model="archiveName"
            type="text"
            placeholder="e.g. Qubit 0-3 Tune-up, Weekly Run..."
            class="w-full box-border text-xs px-3.5 py-2.5 bg-gray-50 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition shadow-2xs"
            @keyup.enter="onSubmit"
          />
        </div>

        <!-- Description (optional) -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 mb-1">
            Description <span class="text-gray-400 font-normal">(optional notes / context)</span>
          </label>
          <textarea
            v-model="archiveDescription"
            rows="2"
            placeholder="Reason for archiving, hardware conditions, setup notes..."
            class="w-full box-border text-xs px-3.5 py-2 bg-gray-50 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition shadow-2xs resize-none"
          ></textarea>
        </div>

        <!-- Filter context summary badge if filters applied -->
        <div v-if="hasFilters" class="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
          <div class="text-[11px] font-semibold text-slate-600 mb-1.5 flex items-center gap-1.5">
            <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Active selection filters (recorded in archive metadata):
          </div>
          <div class="flex flex-wrap gap-1.5 text-[11px]">
            <span v-if="activeFilters.search" class="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700">
              query: "{{ activeFilters.search }}"
            </span>
            <span v-if="activeFilters.subfolder" class="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700">
              folder: {{ activeFilters.subfolder }}
            </span>
            <span v-for="tag in activeFilters.tags || []" :key="'tag-' + tag" class="px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 font-mono">
              tag:{{ tag }}
            </span>
            <span v-for="proto in activeFilters.protocols || []" :key="'proto-' + proto" class="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-mono">
              protocol:{{ proto }}
            </span>
            <span v-for="plat in activeFilters.platforms || []" :key="'plat-' + plat" class="px-2 py-0.5 rounded-md bg-blue-50 text-blue-700">
              platform:{{ plat }}
            </span>
            <span v-for="auth in activeFilters.authors || []" :key="'auth-' + auth" class="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700">
              author:{{ auth }}
            </span>
          </div>
        </div>

        <!-- Remove from active dashboard checkbox -->
        <label class="flex items-start gap-2.5 p-3 rounded-xl bg-amber-50/70 border border-amber-200/80 cursor-pointer">
          <input
            v-model="removeFromActive"
            type="checkbox"
            class="mt-0.5 rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
          />
          <div class="text-xs">
            <span class="font-semibold text-gray-800">Remove from active reports</span>
            <p class="text-[11px] text-gray-500 mt-0.5">
              Reports will be archived into storage and hidden from the dashboard. You can restore them back anytime from the Archives section.
            </p>
          </div>
        </label>

        <div v-if="error" class="p-2.5 bg-red-50 text-red-700 text-xs rounded-xl border border-red-200">
          {{ error }}
        </div>
      </div>

      <div class="mt-6 flex items-center justify-end gap-2">
        <button
          @click="$emit('close')"
          class="px-3.5 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-xl transition cursor-pointer"
        >
          Cancel
        </button>
        <button
          @click="onSubmit"
          :disabled="loading || selectedCount === 0"
          class="px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50"
        >
          <span v-if="loading" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
          Create Archive
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  selectedCount: { type: Number, default: 0 },
  activeFilters: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null }
})

const emit = defineEmits(['close', 'submit'])

const archiveName = ref('')
const archiveDescription = ref('')
const removeFromActive = ref(true)

const hasFilters = computed(() => {
  const f = props.activeFilters || {}
  return (
    Boolean(f.search) ||
    Boolean(f.subfolder) ||
    (f.tags && f.tags.length > 0) ||
    (f.protocols && f.protocols.length > 0) ||
    (f.platforms && f.platforms.length > 0) ||
    (f.authors && f.authors.length > 0)
  )
})

watch(
  () => props.show,
  (val) => {
    if (val) {
      const now = new Date()
      const dStr = now.toISOString().slice(0, 10)
      const tStr = now.toTimeString().slice(0, 5)
      archiveName.value = `Archive ${dStr} ${tStr}`
      archiveDescription.value = ''
      removeFromActive.value = true
    }
  }
)

function onSubmit() {
  if (!props.loading && props.selectedCount > 0) {
    emit('submit', {
      name: archiveName.value.trim() || undefined,
      description: archiveDescription.value.trim() || undefined,
      removeFromActive: removeFromActive.value
    })
  }
}
</script>
