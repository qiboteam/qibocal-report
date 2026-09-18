<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="flex items-center justify-between pb-3 border-b border-gray-100 shrink-0">
        <div class="flex items-center gap-2 text-gray-900 font-bold text-base">
          <svg class="w-5 h-5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          Protocol Documentation Index
        </div>
        <button
          type="button"
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-600 text-lg cursor-pointer bg-transparent border-0 p-0 leading-none"
        >
          &times;
        </button>
      </div>

      <!-- Description -->
      <div class="mt-3 mb-2 shrink-0">
        <p class="text-xs text-gray-500">
          Configure custom protocol documentation URLs for
          <strong class="text-gray-800">{{ serverDisplayName }}</strong>.
          Entries defined here are applied on top of the static index (masking defaults).
        </p>
        <p class="text-[11px] text-gray-400 mt-1 font-mono">
          Base URL: https://qibo.science/qibocal/stable/protocols/
        </p>
      </div>

      <!-- Documentation Rows -->
      <div class="flex-1 overflow-y-auto space-y-2.5 pr-1 py-2 min-h-0">
        <div
          v-if="rows.length === 0"
          class="text-xs text-gray-400 italic bg-gray-50/70 p-4 rounded-xl border border-dashed border-gray-200 text-center"
        >
          No custom protocol documentation mappings configured. The static documentation index is active. Click "+ Add Rule" to add or mask protocol docs.
        </div>

        <div
          v-for="(row, idx) in rows"
          :key="idx"
          class="p-2.5 bg-gray-50/80 rounded-xl border border-gray-200 flex flex-col gap-1.5"
        >
          <div class="flex items-center justify-between gap-2">
            <label class="text-[11px] font-semibold text-gray-600 uppercase tracking-wider">
              Protocol ID / Name
            </label>
            <button
              type="button"
              @click="removeRow(idx)"
              class="text-gray-400 hover:text-red-500 text-xs px-1 cursor-pointer bg-transparent border-0"
              title="Remove rule"
            >
              &times; Remove
            </button>
          </div>
          <input
            v-model="row.protoId"
            type="text"
            placeholder="e.g. qubit_spectroscopy"
            class="w-full px-2.5 py-1.5 bg-white rounded-lg text-xs font-mono text-gray-800 focus:outline-none focus:ring-1 focus:ring-[#833dff]"
          />

          <label class="text-[11px] font-semibold text-gray-600 uppercase tracking-wider mt-1">
            Documentation Path or URL
          </label>
          <input
            v-model="row.docPath"
            type="text"
            placeholder="e.g. characterization/qubit_spectroscopy.html or https://..."
            class="w-full px-2.5 py-1.5 bg-white rounded-lg text-xs font-mono text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#833dff]"
          />
        </div>
      </div>

      <!-- Add Rule Button -->
      <div class="mt-2.5 pt-2 border-t border-gray-100 flex items-center justify-between shrink-0">
        <button
          type="button"
          @click="addRow"
          class="text-xs text-[#833dff] hover:text-purple-800 font-semibold flex items-center gap-1 cursor-pointer bg-transparent border-0 p-0"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Add Rule
        </button>

        <span class="text-[11px] text-gray-400">
          {{ rows.length }} {{ rows.length === 1 ? 'rule' : 'rules' }}
        </span>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="mt-2 p-2 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200 shrink-0">
        {{ error }}
      </div>

      <!-- Footer Buttons -->
      <div class="mt-4 pt-3 border-t border-gray-100 flex items-center justify-end gap-2 shrink-0">
        <button
          type="button"
          @click="$emit('close')"
          class="px-3.5 py-1.5 rounded-xl text-xs font-medium text-gray-600 hover:bg-gray-100 transition cursor-pointer bg-transparent border-0"
        >
          Cancel
        </button>
        <button
          type="button"
          @click="saveMapping"
          :disabled="saving"
          class="px-4 py-1.5 rounded-xl text-xs font-semibold bg-[#833dff] hover:bg-[#722ce6] text-white shadow-2xs transition disabled:opacity-50 cursor-pointer border-0 flex items-center gap-1.5"
        >
          <svg
            v-if="saving"
            class="w-3.5 h-3.5 animate-spin"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ saving ? 'Saving...' : 'Save Index' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { state, updateServer, notifyServerDataChanged } from '../../store.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  server: { type: Object, default: null }
})

const emit = defineEmits(['close', 'saved'])

const rows = ref([])
const saving = ref(false)
const error = ref(null)

const targetServer = computed(() => {
  return props.server || state.activeServer
})

const serverDisplayName = computed(() => {
  return targetServer.value?.name || targetServer.value?.url || 'Active Server'
})

function initFromProps() {
  const current = targetServer.value?.protocol_docs || {}
  rows.value = Object.entries(current).map(([protoId, docPath]) => ({
    protoId,
    docPath: String(docPath || '')
  }))
  error.value = null
}

watch(
  () => props.show,
  (val) => {
    if (val) initFromProps()
  },
  { immediate: true }
)

watch(
  () => targetServer.value,
  () => {
    if (props.show) initFromProps()
  },
  { deep: true }
)

function addRow() {
  rows.value.push({ protoId: '', docPath: '' })
}

function removeRow(idx) {
  rows.value.splice(idx, 1)
}

async function saveMapping() {
  const srv = targetServer.value
  if (!srv?.id) {
    error.value = 'No active server selected.'
    return
  }

  saving.value = true
  error.value = null

  try {
    const protocol_docs = {}
    for (const r of rows.value) {
      const id = (r.protoId || '').trim()
      const path = (r.docPath || '').trim()
      if (id && path) {
        protocol_docs[id] = path
      }
    }

    const updated = await updateServer(srv.id, { protocol_docs })
    if (updated) {
      notifyServerDataChanged()
      emit('saved', updated)
      emit('close')
    } else {
      error.value = 'Failed to update protocol documentation mapping on the server.'
    }
  } catch (err) {
    console.error('Error saving protocol documentation mapping:', err)
    error.value = err.message || 'Failed to save mapping.'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
:deep(input[type="text"]),
input[type="text"] {
  border: none !important;
  outline: none;
  background-color: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.04);
}

:deep(input[type="text"]:focus),
input[type="text"]:focus {
  box-shadow: 0 0 0 1.5px #833dff !important;
}
</style>
