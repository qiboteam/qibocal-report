<template>
  <div class="min-h-screen bg-[#f7f7f7] py-10 px-4 sm:px-6 lg:px-8">
    <div class="max-w-3xl mx-auto">
      <!-- Top Utility Nav: Back to Dashboard & Save Config -->
      <div class="flex items-center justify-between pb-6 mb-6 border-b border-gray-200/60">
        <router-link 
          to="/dashboard"
          class="inline-flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-900 transition"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Dashboard
        </router-link>

        <button 
          @click="handleSaveConfig"
          class="border-0 text-xs font-medium px-3 py-1 rounded-full bg-white hover:bg-gray-50 text-gray-700 shadow-xs hover:shadow-sm transition flex items-center gap-1.5 active:scale-[0.98]"
        >
          <svg class="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
          Save Configuration
        </button>
      </div>

      <!-- Clean Editorial Header -->
      <div class="text-center mb-8">
        <h1 class="text-2xl sm:text-3xl font-semibold text-gray-900 tracking-tight">
          Report Servers
        </h1>
        <p class="mt-1 text-xs sm:text-sm text-gray-500">
          Connect to an instance or manage your registered Qibocal report endpoints.
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
            placeholder="Paste server URL and press Enter (e.g. http://127.0.0.1:8000)..."
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

      <!-- Notification banner if saved -->
      <div 
        v-if="toastMessage" 
        class="mb-4 p-2.5 bg-purple-50/90 rounded-xl text-xs text-purple-900 flex items-center justify-between shadow-2xs"
      >
        <span>✓ {{ toastMessage }}</span>
        <button @click="toastMessage = ''" class="border-0 text-purple-600 hover:text-purple-900 text-sm font-bold leading-none bg-transparent">&times;</button>
      </div>

      <!-- Section Label -->
      <div class="flex items-center justify-between mb-3 px-0.5">
        <h2 class="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
          Registered Instances ({{ servers.length }})
        </h2>
      </div>

      <!-- Grid of Lightweight Server Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        <server-card 
          v-for="server in servers"
          :key="server.id"
          :server="server"
          :is-active="server.id === activeServer?.id"
          @select="selectAndNavigate"
          @edit="openEditModal"
          @delete="handleDelete"
        />
      </div>

      <!-- Refined Edit Modal -->
      <server-modal 
        v-if="modalOpen"
        :server="editingServer"
        @close="modalOpen = false"
        @save="saveModalServer"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { state, addServer, updateServer, deleteServer, setActiveServer, persistServersConfig } from '../store.js'
import ServerCard from '../components/ServerCard.vue'
import ServerModal from '../components/ServerModal.vue'

const router = useRouter()
const newServerUrl = ref('')
const modalOpen = ref(false)
const editingServer = ref(null)
const toastMessage = ref('')

const servers = computed(() => state.servers)
const activeServer = computed(() => state.activeServer)

async function handleQuickAdd() {
  if (!newServerUrl.value.trim()) return
  const created = await addServer(newServerUrl.value.trim())
  newServerUrl.value = ''
  if (created) {
    toastMessage.value = `Server '${created.name}' registered.`
    setActiveServer(created)
  }
}

function selectAndNavigate(server) {
  setActiveServer(server)
  router.push('/dashboard')
}

function openEditModal(server) {
  editingServer.value = server
  modalOpen.value = true
}

async function saveModalServer(updatedData) {
  if (updatedData.id) {
    await updateServer(updatedData.id, updatedData)
    toastMessage.value = `Server updated.`
  } else {
    await addServer(updatedData.url, updatedData.name, updatedData.description, updatedData.avatar)
    toastMessage.value = `Server registered.`
  }
  modalOpen.value = false
}

async function handleDelete(server) {
  if (confirm(`Remove server "${server.name}"?`)) {
    await deleteServer(server.id)
    toastMessage.value = `Server removed.`
  }
}

async function handleSaveConfig() {
  const res = await persistServersConfig()
  if (res && res.saved) {
    toastMessage.value = `Configuration saved to ~/.config/qibocal-report/servers.json`
  }
}
</script>
