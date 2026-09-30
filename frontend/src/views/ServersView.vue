<template>
  <div class="min-h-screen bg-[#f7f7f7] py-10 px-4 sm:px-6 lg:px-8">
    <div class="max-w-3xl mx-auto">
      <!-- Top Utility Nav: Documentation, Dashboard (if auth), and Server Admin (if admin) -->
      <div class="flex items-center justify-between pb-6 mb-6 border-b border-gray-200/60">
        <div>
          <router-link
            v-if="canAccessDashboard"
            to="/dashboard"
            class="inline-flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-900 transition"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Dashboard
          </router-link>
        </div>

        <div class="flex items-center gap-2.5">
          <!-- Documentation Link - Always accessible to everyone -->
          <router-link
            to="/docs"
            class="inline-flex items-center gap-1.5 text-xs font-medium text-gray-600 hover:text-[#833dff] transition bg-white hover:bg-purple-50/60 px-3 py-1.5 rounded-xl border border-gray-200/80 shadow-2xs"
            title="Browse documentation, user guides, and administrator guides"
          >
            <svg class="w-3.5 h-3.5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            Documentation
          </router-link>
        </div>
      </div>

      <!-- Clean Editorial Header -->
      <div class="text-center mb-8">
        <h1 class="text-2xl sm:text-3xl font-semibold text-gray-900 tracking-tight">
          Report Servers
        </h1>
        <p class="mt-1 text-xs sm:text-sm text-gray-500">
          Connect to an instance, paste an invite link, or manage your registered Qibocal report endpoints.
        </p>
      </div>

      <!-- Seamless Paste Box without borders -->
      <div class="max-w-xl mx-auto mb-8">
        <form
          @submit.prevent="handleQuickAdd"
          class="border-0 relative flex items-center bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow p-1.5 pl-4"
        >
          <svg class="w-4 h-4 text-gray-400 shrink-0 mr-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          <input
            v-model="newServerUrl"
            type="text"
            placeholder="Paste server URL or invite link"
            class="border-0 outline-none w-full bg-transparent text-xs sm:text-sm text-gray-900 placeholder-gray-400 focus:outline-none py-1.5"
            required
          />
          <button
            type="submit"
            :disabled="!newServerUrl.trim()"
            class="border-0 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-[#833dff] text-white hover:bg-[#722ce6] active:scale-[0.98] disabled:opacity-35 transition shrink-0 shadow-2xs"
          >
            Connect
          </button>
        </form>
      </div>

      <!-- Error banner if auth failed or forbidden -->
      <div
        v-if="state.auth?.errorMessage"
        class="mb-4 p-3 bg-red-50 text-red-700 rounded-xl text-xs flex items-center justify-between shadow-2xs border-0 animate-fade-in"
      >
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4 text-red-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span class="font-medium">{{ state.auth.errorMessage }}</span>
        </div>
        <button
          @click="state.auth.errorMessage = ''"
          class="border-0 text-red-500 hover:text-red-700 text-sm font-bold leading-none bg-transparent cursor-pointer"
        >&times;</button>
      </div>

      <!-- Notification banner if saved -->
      <div
        v-if="toastMessage"
        class="mb-4 p-2.5 bg-purple-50/90 rounded-xl text-xs text-purple-900 flex items-center justify-between shadow-2xs"
      >
        <span>✓ {{ toastMessage }}</span>
        <button @click="toastMessage = ''" class="border-0 text-purple-600 hover:text-purple-900 text-sm font-bold leading-none bg-transparent">&times;</button>
      </div>

      <!-- Section Label with Drag Hint -->
      <div class="flex items-center justify-between mb-3 px-0.5">
        <h2 class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
          Registered Instances ({{ servers.length }})
        </h2>
        <span v-if="servers.length > 1" class="text-[10px] text-gray-400 flex items-center gap-1 font-medium">
          <svg class="w-3 h-3 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
            <path d="M7 2a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 2zm0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 8zm0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 14zm6-12a2 2 0 1 0 .001 4.001A2 2 0 0 0 13 2zm0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 13 8zm0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 13 14z" />
          </svg>
          Drag cards to swap
        </span>
      </div>

      <!-- Grid of Lightweight Server Cards (Draggable / Fixed Grid) -->
      <div v-if="servers.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        <div
          v-for="(server, index) in servers"
          :key="server.id"
          draggable="true"
          @dragstart="onDragStart($event, index)"
          @dragover.prevent="onDragOver($event, index)"
          @dragenter.prevent="onDragEnter($event, index)"
          @dragleave="onDragLeave($event, index)"
          @drop="onDrop($event, index)"
          @dragend="onDragEnd"
          class="transition-all duration-150 rounded-2xl cursor-grab active:cursor-grabbing select-none"
          :class="{
            'opacity-40 scale-[0.98]': draggedIndex === index,
            'ring-2 ring-[#833dff] ring-offset-2 scale-[1.01] shadow-md': dropTargetIndex === index && draggedIndex !== index
          }"
        >
          <server-card
            :server="server"
            :is-active="server.id === activeServer?.id"
            @select="selectAndNavigate"
            @logout="handleLogout"
            @edit="openEditModal"
            @delete="handleDelete"
            @administer="navigateToAdmin"
          />
        </div>
      </div>

      <!-- Empty State when no servers are registered yet -->
      <div v-else class="text-center py-12 px-4 bg-white rounded-2xl border border-gray-100 shadow-xs">
        <div class="w-12 h-12 rounded-2xl bg-purple-50 text-[#833dff] flex items-center justify-center mx-auto mb-3">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
        </div>
        <h3 class="text-sm font-semibold text-gray-900">No servers connected</h3>
        <p class="mt-1 text-xs text-gray-500 max-w-sm mx-auto">
          Paste a server address or invitation link above to register and access your reports.
        </p>
      </div>

      <div class="flex items-center justify-end gap-2 mt-4">
        <button
          type="button"
          @click="saveClientState"
          aria-label="Save client state"
          title="Save client state to a JSON file (sign-in sessions excluded)"
          class="p-2 rounded-xl bg-white border border-gray-200 text-gray-500 hover:text-[#833dff] transition"
        >
          <svg class="w-4 h-4" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v4a1 1 0 001 1h14a1 1 0 001-1v-4M12 3v12m-5-5l5 5 5-5" />
          </svg>
        </button>
        <button
          type="button"
          @click="stateFileInput.click()"
          :disabled="loadingClientState"
          :aria-label="loadingClientState ? 'Loading client state' : 'Load client state'"
          title="Load client state from a JSON file and replace this browser's settings"
          class="p-2 rounded-xl bg-white border border-gray-200 text-gray-500 hover:text-[#833dff] transition disabled:opacity-50"
        >
          <svg class="w-4 h-4" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v4a1 1 0 001 1h14a1 1 0 001-1v-4M12 15V3m-5 5l5-5 5 5" />
          </svg>
        </button>
        <input ref="stateFileInput" type="file" accept=".json,application/json" class="hidden" @change="loadClientState" />
      </div>

      <!-- Refined Edit Modal -->
      <server-modal
        v-if="modalOpen"
        :server="editingServer"
        @close="modalOpen = false"
        @save="saveModalServer"
        @directory-changed="handleDirectoryChanged"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  state,
  fetchServers,
  addServer,
  updateServer,
  deleteServer,
  setActiveServer,
  canAccessDashboard,
  isAuthenticated,
  logoutActiveServer,
  saveStoredServers,
  exportClientState,
  importClientState
} from '../store.js'
import { parseClientState } from '../utils/clientState.js'
import { parseServerAndInvite, normalizeUrl } from '../utils/url.js'
import ServerCard from '../components/ServerCard.vue'
import ServerModal from '../components/ServerModal.vue'

const router = useRouter()
const newServerUrl = ref('')
const modalOpen = ref(false)
const editingServer = ref(null)
const toastMessage = ref('')
const stateFileInput = ref(null)
const loadingClientState = ref(false)

function showError(error) {
  toastMessage.value = ''
  state.auth.errorMessage = error.message || 'Unable to save client settings.'
}

function saveClientState() {
  let url
  try {
    const data = JSON.stringify(exportClientState(), null, 2)
    url = URL.createObjectURL(new Blob([data], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'qibocal-report-client.json'
    link.click()
    state.auth.errorMessage = ''
    toastMessage.value = 'Client state saved without sign-in sessions.'
  } catch (error) {
    showError(error)
  } finally {
    if (url) URL.revokeObjectURL(url)
  }
}

async function loadClientState(event) {
  const file = event.target.files?.[0]
  if (!file) return
  loadingClientState.value = true
  try {
    const saved = parseClientState(JSON.parse(await file.text()))
    if (!confirm('Replace this browser\'s client settings with the saved state? Current sign-in sessions will be cleared.')) return
    importClientState(saved)
    modalOpen.value = false
    editingServer.value = null
    toastMessage.value = 'Client state loaded. Sign in again to authenticated servers.'
  } catch (error) {
    showError(error)
  } finally {
    event.target.value = ''
    loadingClientState.value = false
  }
}

const draggedIndex = ref(null)
const dropTargetIndex = ref(null)

const servers = computed(() => state.servers)
const activeServer = computed(() => state.activeServer)

function onDragStart(e, index) {
  draggedIndex.value = index
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(index))
}

function onDragOver(e, index) {
  e.dataTransfer.dropEffect = 'move'
}

function onDragEnter(e, index) {
  if (draggedIndex.value !== null && draggedIndex.value !== index) {
    dropTargetIndex.value = index
  }
}

function onDragLeave(e, index) {
  if (dropTargetIndex.value === index) {
    dropTargetIndex.value = null
  }
}

async function onDrop(e, targetIndex) {
  e.preventDefault()
  const rawFrom = draggedIndex.value !== null ? draggedIndex.value : parseInt(e.dataTransfer.getData('text/plain'), 10)

  if (rawFrom !== null && !isNaN(rawFrom) && rawFrom !== targetIndex && rawFrom >= 0 && rawFrom < state.servers.length) {
    const updated = [...state.servers]
    const temp = updated[rawFrom]
    updated[rawFrom] = updated[targetIndex]
    updated[targetIndex] = temp
    try {
      saveStoredServers(updated)
      state.servers = updated
    } catch (err) {
      showError(err)
    }
  }

  draggedIndex.value = null
  dropTargetIndex.value = null
}

function onDragEnd() {
  draggedIndex.value = null
  dropTargetIndex.value = null
}

function handleDirectoryChanged({ server, dirInfo }) {
  const targetName = dirInfo?.relative_current || 'root'
  toastMessage.value = `Folder for "${server?.name || 'Server'}" set to ${targetName}.`
  fetchServers()
}

async function handleQuickAdd() {
  try {
    const input = newServerUrl.value.trim()
    if (!input) return

    const parsed = parseServerAndInvite(input)
    const targetUrl = parsed.url || input

    let targetServer = state.servers.find(s => normalizeUrl(s.url) === normalizeUrl(targetUrl))
    if (!targetServer) {
      targetServer = await addServer(targetUrl)
    }

    newServerUrl.value = ''
    if (targetServer) {
      setActiveServer(targetServer)
      if (parsed.inviteToken) {
        state.auth.registerData = {
          token: parsed.inviteToken,
          server: targetServer,
          serverUrl: targetServer.url
        }
        state.auth.showRegisterModal = true
      } else if (parsed.resetToken) {
        state.auth.registerData = {
          token: parsed.resetToken,
          server: targetServer,
          serverUrl: targetServer.url
        }
        state.auth.showRegisterModal = true
      } else {
        toastMessage.value = `Server '${targetServer.name}' connected.`
      }
    }
  } catch (error) {
    showError(error)
  }
}

function navigateToAdmin(server) {
  if (server) setActiveServer(server)
  router.push('/admin')
}

async function selectAndNavigate(server) {
  
  // Check if server is reachable before navigating
  try {
    const normalized = normalizeUrl(server?.url)
    const healthUrl = normalized ? `${normalized}/api/health` : '/api/health'
    const healthRes = await fetch(healthUrl, { signal: AbortSignal.timeout(5000), cache: 'no-store' })
    
    if (!healthRes.ok) {
      toastMessage.value = ''
      state.auth.errorMessage = `Cannot connect to "${server.name}". The server is unreachable.`
      return
    }
  } catch (err) {
    toastMessage.value = ''
    state.auth.errorMessage = `Cannot connect to "${server.name}": ${err.message || 'Network error'}`
    return
  }
  
  if (!await setActiveServer(server)) return
  if (!isAuthenticated.value) {
    toastMessage.value = ''
    state.auth.showLoginModal = true
    return
  }
  router.push('/dashboard')
}

function handleLogout(server) {
  logoutActiveServer(server)
  toastMessage.value = `Logged out of "${server.name}". Click the server to sign in again.`
}

function openEditModal(server) {
  editingServer.value = server
  modalOpen.value = true
}

async function saveModalServer(updatedData) {
  try {
    if (updatedData.id) {
      const updated = await updateServer(updatedData.id, updatedData)
      if (!updated) throw new Error('Server is no longer registered.')
      toastMessage.value = `Server updated.`
    } else {
      const created = await addServer(updatedData)
      if (created) {
        setActiveServer(created)
        toastMessage.value = `Server registered.`
      }
    }
    modalOpen.value = false
  } catch (error) {
    showError(error)
  }
}

async function handleDelete(server) {
  if (confirm(`Remove server "${server.name}"?`)) {
    try {
      if (!await deleteServer(server.id)) throw new Error('Server is no longer registered.')
      state.auth.errorMessage = ''
      toastMessage.value = `Server removed from this browser.`
    } catch (error) {
      showError(error)
    }
  }
}
</script>
