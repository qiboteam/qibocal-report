<!--
  A folder on the server, picked by walking its tree: for installing Qibocal
  from a checkout there. Folders that look like a Python project are marked.
-->
<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-2xl max-w-lg w-full p-5 shadow-2xl border border-black/[0.08] flex flex-col max-h-[85vh] overflow-hidden">
      <div class="flex items-start justify-between gap-3 mb-3">
        <div class="min-w-0">
          <h2 class="text-sm font-semibold text-gray-900">Choose a folder on the server</h2>
          <p class="text-xs text-gray-500 mt-0.5">The Qibocal checkout to install from. Folders holding a Python project are marked.</p>
        </div>
        <button type="button" class="border-0 w-6 h-6 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition cursor-pointer" aria-label="Close" @click="$emit('close')">&times;</button>
      </div>

      <form class="flex items-center gap-2 mb-3" @submit.prevent="browse(typed)">
        <input
          v-model.trim="typed"
          type="text"
          class="flex-1 min-w-0 px-2.5 py-1.5 rounded-lg border border-gray-200 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-[#833dff]/40"
          placeholder="/home/me/qibocal"
          aria-label="Path on the server"
          spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off"
        />
        <button type="submit" class="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-white border border-gray-200 hover:border-purple-300 cursor-pointer">Go</button>
      </form>

      <p v-if="error" class="text-xs text-red-700 mb-2" role="alert">{{ error }}</p>
      <p v-else-if="loading" class="text-xs text-gray-400 mb-2" role="status">Reading…</p>

      <div class="min-h-0 flex-1 overflow-y-auto rounded-xl border border-gray-100 divide-y divide-gray-100">
        <button
          v-if="parent"
          type="button"
          class="w-full text-left px-3 py-2 text-xs text-gray-500 hover:bg-purple-50 cursor-pointer font-mono"
          @click="browse(parent)"
        >‥ up</button>
        <button
          v-for="entry in entries"
          :key="entry.path"
          type="button"
          class="w-full text-left px-3 py-2 text-xs hover:bg-purple-50 cursor-pointer flex items-center gap-2"
          :class="entry.project ? 'text-[#3b107e] font-medium' : 'text-gray-700'"
          @click="browse(entry.path)"
          @dblclick="choose(entry.path)"
        >
          <span class="font-mono truncate">{{ entry.name }}</span>
          <span v-if="entry.project" class="ml-auto text-[10px] uppercase tracking-wide text-[#833dff]">project</span>
        </button>
        <p v-if="!loading && !entries.length && !error" class="px-3 py-3 text-xs text-gray-400">No folders here.</p>
      </div>

      <div class="flex items-center gap-2 mt-3 text-xs">
        <code class="flex-1 min-w-0 truncate text-gray-600" :title="current">{{ current }}</code>
        <button type="button" class="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-100 cursor-pointer" @click="$emit('close')">Cancel</button>
        <button
          type="button"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold bm-btn-primary cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          :disabled="!current || !isProject"
          :title="isProject ? 'Install Qibocal from this folder' : 'This folder has no pyproject.toml or setup.py'"
          @click="choose(current)"
        >Use this folder</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { apiBrowseServerFolders } from '../../api.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  initialPath: { type: String, default: '' },
  server: { type: Object, default: null }
})
const emit = defineEmits(['close', 'select'])

const loading = ref(false)
const error = ref('')
const current = ref('')
const parent = ref(null)
const entries = ref([])
const isProject = ref(false)
const typed = ref('')

async function browse(path) {
  loading.value = true
  error.value = ''
  try {
    const response = await apiBrowseServerFolders(path, props.server || undefined)
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(body.detail || `The server could not list the folder (${response.status}).`)
    }
    const data = await response.json()
    current.value = data.path
    parent.value = data.parent
    entries.value = data.entries || []
    isProject.value = Boolean(data.project)
    typed.value = data.path
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function choose(path) {
  emit('select', path)
  emit('close')
}

watch(() => props.show, open => {
  if (open) browse(props.initialPath || '')
})
</script>
