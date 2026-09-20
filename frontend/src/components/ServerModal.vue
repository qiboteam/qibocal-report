<template>
  <div class="fixed inset-0 bg-black/25 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
    <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-5 relative border border-black/[0.08]">
      <!-- Header -->
      <div class="flex items-center justify-between pb-3 border-b border-gray-100">
        <h2 class="text-sm font-semibold text-gray-900">
          {{ isEdit ? 'Edit Server Configuration' : 'Add Server Instance' }}
        </h2>
        <button
          @click="$emit('close')"
          class="border-0 w-6 h-6 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="submitForm" class="mt-3.5 space-y-3.5">
        <!-- URL Field -->
        <div>
          <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1">
            Endpoint URL
          </label>
          <input
            v-model="form.url"
            type="text"
            required
            placeholder="http://127.0.0.1:8000"
            class="w-full px-3 py-2 bg-gray-50/70 rounded-lg text-xs font-mono text-gray-900 transition"
          />
        </div>

        <!-- Name Field -->
        <div>
          <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1">
            Display Name
          </label>
          <input
            v-model="form.name"
            type="text"
            placeholder="e.g. quantum-curie"
            class="w-full px-3 py-2 bg-gray-50/70 rounded-lg text-xs text-gray-900 transition"
          />
        </div>

        <!-- Description -->
        <div>
          <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1">
            Description
          </label>
          <textarea
            v-model="form.description"
            rows="2"
            placeholder="Lab QPU calibration archive..."
            class="w-full px-3 py-2 bg-gray-50/70 rounded-lg text-xs text-gray-900 transition resize-none"
          ></textarea>
        </div>

        <!-- Avatar Selection (Issue #4) -->
        <div>
          <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">
            Abstract Icon
          </label>
          <div class="grid grid-cols-5 gap-2">
            <div
              v-for="key in AVATAR_KEYS"
              :key="key"
              @click="form.avatar = key"
              class="w-10 h-10 p-1 rounded-lg cursor-pointer border transition flex items-center justify-center bg-gray-50/50"
              :class="form.avatar === key ? 'border-[#833dff] bg-purple-50/80 ring-2 ring-[#833dff]/20' : 'border-gray-200 hover:border-gray-300'"
              :title="key"
            >
              <div class="w-8 h-8" v-html="renderAvatar(key)"></div>
            </div>
          </div>
        </div>

        <!-- Report Root Directory Section (Edit Server Configuration) -->
        <div v-if="isEdit" class="pt-2 border-t border-gray-100">
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider">
              Report Directory
            </label>
            <span v-if="dirInfo?.reports_count !== undefined" class="text-[10px] font-mono font-medium text-[#833dff] bg-purple-50 px-1.5 py-0.2 rounded border border-purple-100">
              {{ dirInfo.reports_count }} {{ dirInfo.reports_count === 1 ? 'report' : 'reports' }}
            </span>
          </div>

          <div class="p-2.5 bg-gray-50/90 rounded-xl border border-gray-200 flex items-center justify-between gap-2.5">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5 text-xs text-gray-800 font-semibold truncate">
                <svg class="w-4 h-4 text-[#833dff] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                <span class="truncate" :title="dirInfo?.current_root || 'Connecting to server...'">
                  {{ dirInfo?.relative_current ? dirInfo.relative_current : (dirInfo?.current_root ? 'Original root folder' : 'Checking...') }}
                </span>
                <span v-if="dirInfo && !dirInfo.relative_current" class="text-[9px] font-bold bg-gray-200/80 text-gray-600 px-1 py-0.2 rounded font-mono shrink-0">
                  spawn-root
                </span>
              </div>
              <p class="text-[10px] font-mono text-gray-400 truncate mt-0.5" :title="dirInfo?.current_root">
                {{ dirInfo?.current_root || (isServerOffline ? 'Server offline' : 'Loading path...') }}
              </p>
            </div>

            <!-- Further button to open tiny file browser -->
            <button
              type="button"
              @click="showBrowser = true"
              :disabled="dirLoading || isServerOffline"
              class="border border-purple-200 bg-white hover:bg-purple-50 hover:border-purple-300 text-[#833dff] px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-2xs transition disabled:opacity-40 disabled:pointer-events-none cursor-pointer shrink-0"
              title="Open file browser to change report directory"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
              </svg>
              Browse Folders
            </button>
          </div>

          <p v-if="isServerOffline" class="text-[11px] text-amber-600 mt-1">
            Server is unreachable. Start the server to browse or change its directory.
          </p>
        </div>

        <!-- Author Identities (Alias Mapping) -->
        <div class="pt-2 border-t border-gray-100">
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider">
              Author Identities
            </label>
            <button
              type="button"
              @click="addIdentityRow"
              class="text-[11px] text-[#833dff] hover:text-[#722ce6] font-medium flex items-center gap-1 cursor-pointer"
            >
              + Add Mapping
            </button>
          </div>
          <p class="text-[11px] text-gray-400 mb-2">
            Map multiple author identifiers or usernames to a single canonical identity.
          </p>

          <div v-if="identityRows.length === 0" class="text-[11px] text-gray-400 italic bg-gray-50/60 p-2.5 rounded-lg border border-dashed border-gray-200 text-center">
            No author identity mappings configured
          </div>

          <div v-else class="space-y-2 max-h-32 overflow-y-auto pr-1">
            <div
              v-for="(row, idx) in identityRows"
              :key="idx"
              class="flex items-center gap-1.5 p-1.5 bg-gray-100/60 rounded-xl border-0 text-xs"
            >
              <input
                v-model="row.canonical"
                type="text"
                placeholder="Canonical name (e.g. Alice)"
                class="flex-1 px-2.5 py-1.5 bg-white rounded-lg text-xs border-0 shadow-2xs"
              />
              <input
                v-model="row.aliases"
                type="text"
                placeholder="Aliases (e.g. alice, a.smith)"
                class="flex-1 px-2.5 py-1.5 bg-white rounded-lg text-xs font-mono border-0 shadow-2xs"
              />
              <button
                type="button"
                @click="removeIdentityRow(idx)"
                class="text-gray-400 hover:text-red-500 p-1 text-sm leading-none cursor-pointer"
                title="Remove mapping"
              >
                &times;
              </button>
            </div>
          </div>
        </div>

        <!-- Protocol Documentation Index (Overrides static docs) -->
        <div class="pt-2 border-t border-gray-100">
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider">
              Custom Protocol Docs
            </label>
            <button
              type="button"
              @click="addProtocolDocRow"
              class="text-[11px] text-[#833dff] hover:text-[#722ce6] font-medium flex items-center gap-1 cursor-pointer bg-transparent border-0 p-0"
            >
              + Add Rule
            </button>
          </div>
          <p class="text-[11px] text-gray-400 mb-2">
            Configure custom protocol documentation URLs or paths for this server (masks default static index).
          </p>

          <div v-if="protocolDocRows.length === 0" class="text-[11px] text-gray-400 italic bg-gray-50/60 p-2.5 rounded-lg border-0 text-center">
            No custom protocol docs configured
          </div>

          <div v-else class="space-y-2 max-h-32 overflow-y-auto pr-1">
            <div
              v-for="(row, idx) in protocolDocRows"
              :key="idx"
              class="flex items-center gap-1.5 p-1.5 bg-gray-100/60 rounded-xl border-0 text-xs"
            >
              <input
                v-model="row.protoId"
                type="text"
                placeholder="Protocol ID (e.g. rabi)"
                class="w-1/3 px-2.5 py-1.5 bg-white rounded-lg text-xs font-mono border-0 shadow-2xs"
              />
              <input
                v-model="row.docPath"
                type="text"
                placeholder="Relative path or full URL"
                class="flex-1 px-2.5 py-1.5 bg-white rounded-lg text-xs font-mono border-0 shadow-2xs"
              />
              <button
                type="button"
                @click="removeProtocolDocRow(idx)"
                class="text-gray-400 hover:text-red-500 p-1 text-sm leading-none cursor-pointer bg-transparent border-0"
                title="Remove rule"
              >
                &times;
              </button>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="pt-3 border-t border-gray-100 flex items-center justify-end gap-2">
          <button
            type="button"
            @click="$emit('close')"
            class="border-0 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-100 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="border-0 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-[#833dff] text-white hover:bg-[#722ce6] active:scale-[0.98] transition shadow-2xs"
          >
            {{ isEdit ? 'Save Changes' : 'Register' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Tiny File Browser Modal for selecting server directory -->
    <directory-browser-modal
      :show="showBrowser"
      :server-url="form.url || props.server?.url || ''"
      :initial-path="dirInfo?.relative_current || ''"
      @close="showBrowser = false"
      @select="onDirectorySelected"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { AVATAR_KEYS, renderAvatar } from './Avatars.js'
import DirectoryBrowserModal from './modals/DirectoryBrowserModal.vue'
import { state, normalizeUrl, notifyServerDataChanged } from '../store.js'

const props = defineProps({
  server: { type: Object, default: null }
})

const emit = defineEmits(['close', 'save', 'directory-changed'])

const isEdit = computed(() => !!props.server?.id)

const form = reactive({
  id: props.server?.id || null,
  url: props.server?.url || '',
  name: props.server?.name || '',
  description: props.server?.description || '',
  avatar: props.server?.avatar || 'quantum-ring'
})

const identityRows = ref(
  props.server?.author_identities
    ? Object.entries(props.server.author_identities).map(([canonical, aliases]) => ({
        canonical,
        aliases: Array.isArray(aliases) ? aliases.join(', ') : String(aliases || '')
      }))
    : []
)

const protocolDocRows = ref(
  props.server?.protocol_docs
    ? Object.entries(props.server.protocol_docs).map(([protoId, docPath]) => ({
        protoId,
        docPath: String(docPath || '')
      }))
    : []
)

// Server Directory Management State
const showBrowser = ref(false)
const dirInfo = ref(null)
const dirLoading = ref(false)
const isServerOffline = ref(false)

async function fetchDirectoryInfo() {
  const url = props.server?.url || form.url
  if (!url) return
  dirLoading.value = true
  isServerOffline.value = false
  try {
    const base = normalizeUrl(url)
    const targetUrl = `${base}/api/server/directory`
    const res = await fetch(targetUrl, { signal: AbortSignal.timeout(4000) })
    if (res.ok) {
      dirInfo.value = await res.json()
      isServerOffline.value = false
    } else {
      isServerOffline.value = true
    }
  } catch {
    isServerOffline.value = true
  } finally {
    dirLoading.value = false
  }
}

function onDirectorySelected({ path, dirInfo: newInfo }) {
  dirInfo.value = newInfo
  if (state.activeServer?.id === props.server?.id) {
    notifyServerDataChanged()
  }
  emit('directory-changed', { server: props.server, dirInfo: newInfo })
}

watch(
  () => props.server?.id,
  () => {
    if (isEdit.value) {
      fetchDirectoryInfo()
    }
  }
)

onMounted(() => {
  if (isEdit.value) {
    fetchDirectoryInfo()
  }
})

function addIdentityRow() {
  identityRows.value.push({ canonical: '', aliases: '' })
}

function removeIdentityRow(idx) {
  identityRows.value.splice(idx, 1)
}

function addProtocolDocRow() {
  protocolDocRows.value.push({ protoId: '', docPath: '' })
}

function removeProtocolDocRow(idx) {
  protocolDocRows.value.splice(idx, 1)
}

function submitForm() {
  const author_identities = {}
  for (const row of identityRows.value) {
    const c = (row.canonical || '').trim()
    if (c) {
      const aliasList = (row.aliases || '')
        .split(',')
        .map(a => a.trim())
        .filter(Boolean)
      author_identities[c] = aliasList
    }
  }

  const protocol_docs = {}
  for (const row of protocolDocRows.value) {
    const id = (row.protoId || '').trim()
    const path = (row.docPath || '').trim()
    if (id && path) {
      protocol_docs[id] = path
    }
  }

  emit('save', {
    ...form,
    url: normalizeUrl(form.url),
    author_identities,
    protocol_docs
  })
}
</script>

<style scoped>
:deep(input[type="text"]),
:deep(textarea),
input[type="text"],
textarea {
  border: none !important;
  outline: none;
  background-color: #ffffff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.04);
}

:deep(input[type="text"]:focus),
:deep(textarea:focus),
input[type="text"]:focus,
textarea:focus {
  box-shadow: 0 0 0 1.5px #833dff !important;
}
</style>
