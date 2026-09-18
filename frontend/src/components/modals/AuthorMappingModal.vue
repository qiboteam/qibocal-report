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
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          Author Identities Mapping
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
          Map author aliases, usernames, or typos to a single canonical name for
          <strong class="text-gray-800">{{ serverDisplayName }}</strong>.
        </p>
      </div>

      <!-- Mapping Rows -->
      <div class="flex-1 overflow-y-auto space-y-2.5 pr-1 py-2 min-h-0">
        <div
          v-if="rows.length === 0"
          class="text-xs text-gray-400 italic bg-gray-50/70 p-4 rounded-xl border border-dashed border-gray-200 text-center"
        >
          No author identity mappings configured yet. Click "+ Add Mapping" below to define canonical names and their aliases.
        </div>

        <div
          v-for="(row, idx) in rows"
          :key="idx"
          class="p-2.5 bg-gray-50/80 rounded-xl border border-gray-200 flex flex-col gap-1.5"
        >
          <div class="flex items-center justify-between gap-2">
            <label class="text-[11px] font-semibold text-gray-600 uppercase tracking-wider">
              Canonical Identity
            </label>
            <button
              type="button"
              @click="removeRow(idx)"
              class="text-gray-400 hover:text-red-500 text-xs px-1 cursor-pointer bg-transparent border-0"
              title="Remove mapping"
            >
              &times; Remove
            </button>
          </div>
          <input
            v-model="row.canonical"
            type="text"
            placeholder="e.g. Alessandro Candido"
            class="w-full px-2.5 py-1.5 bg-white rounded-lg text-xs font-medium focus:outline-none focus:ring-1 focus:ring-[#833dff]"
          />
          <label class="text-[11px] font-semibold text-gray-600 uppercase tracking-wider mt-1">
            Aliases / Usernames <span class="text-gray-400 font-normal normal-case">(comma separated)</span>
          </label>
          <input
            v-model="row.aliases"
            type="text"
            placeholder="e.g. alessandro.candido, alecandido, acandido"
            class="w-full px-2.5 py-1.5 bg-white rounded-lg text-xs font-mono text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#833dff]"
          />
        </div>
      </div>

      <!-- Add Mapping Button -->
      <div class="mt-2.5 pt-2 border-t border-gray-100 flex items-center justify-between shrink-0">
        <button
          type="button"
          @click="addRow"
          class="text-xs text-[#833dff] hover:text-purple-800 font-semibold flex items-center gap-1 cursor-pointer bg-transparent border-0 p-0"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Add Mapping
        </button>

        <span class="text-[11px] text-gray-400">
          {{ rows.length }} {{ rows.length === 1 ? 'rule' : 'rules' }}
        </span>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="mt-2 p-2 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200 shrink-0">
        {{ error }}
      </div>

      <!-- Actions -->
      <div class="mt-4 pt-3 border-t border-gray-100 flex items-center justify-end gap-2 shrink-0">
        <button
          type="button"
          @click="$emit('close')"
          class="border-0 px-3.5 py-1.5 rounded-xl text-xs font-medium text-gray-600 hover:bg-gray-100 transition cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="button"
          @click="saveMapping"
          :disabled="saving"
          class="border-0 px-4 py-1.5 rounded-xl text-xs font-semibold bg-[#833dff] text-white hover:bg-[#722ce6] transition shadow-2xs cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
        >
          <svg v-if="saving" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          {{ saving ? 'Saving...' : 'Save Mapping' }}
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

const targetServer = computed(() => {
  return props.server || state.activeServer || (state.servers.length > 0 ? state.servers[0] : null)
})

const serverDisplayName = computed(() => {
  return targetServer.value?.name || targetServer.value?.url || 'active server'
})

const rows = ref([])
const error = ref('')
const saving = ref(false)

function initRows() {
  error.value = ''
  const identities = targetServer.value?.author_identities || {}
  rows.value = Object.entries(identities).map(([canonical, aliases]) => ({
    canonical,
    aliases: Array.isArray(aliases) ? aliases.join(', ') : String(aliases || '')
  }))
}

watch(() => props.show, (val) => {
  if (val) {
    initRows()
  }
})

watch(() => targetServer.value, () => {
  if (props.show) {
    initRows()
  }
})

function addRow() {
  rows.value.push({ canonical: '', aliases: '' })
}

function removeRow(idx) {
  rows.value.splice(idx, 1)
}

async function saveMapping() {
  error.value = ''
  saving.value = true
  try {
    const srv = targetServer.value
    if (!srv || !srv.id) {
      error.value = 'No active server found to update.'
      saving.value = false
      return
    }

    const mapping = {}
    for (const r of rows.value) {
      const canonical = (r.canonical || '').trim()
      if (!canonical) continue
      const aliasList = (r.aliases || '')
        .split(',')
        .map(a => a.trim())
        .filter(Boolean)
      mapping[canonical] = aliasList
    }

    const updated = await updateServer(srv.id, { author_identities: mapping })
    if (updated) {
      notifyServerDataChanged()
      emit('saved', updated)
      emit('close')
    } else {
      error.value = 'Failed to update author mapping on the server.'
    }
  } catch (err) {
    console.error('Error saving author identities mapping:', err)
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
