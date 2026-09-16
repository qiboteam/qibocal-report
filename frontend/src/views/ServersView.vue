<template>
  <div class="min-h-screen bg-[#f7f7f7] py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-4xl mx-auto">
      <!-- Title & Branding -->
      <div class="text-center mb-10">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-white shadow-md text-[#833dff] mb-4">
          <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="9" stroke-width="2" />
            <path stroke-width="2" d="M12 3a9 9 0 019 9m-9 9a9 9 0 01-9-9" />
            <circle cx="12" cy="12" r="3" fill="#833dff" />
          </svg>
        </div>
        <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 tracking-tight">
          Qibocal Report Servers
        </h1>
        <p class="mt-2 text-sm text-gray-600 max-w-lg mx-auto">
          Manage your registered Qibocal servers or connect to a new instance.
        </p>
      </div>

      <!-- Central Text Box: Paste & Enter should be sufficient (Issue #4) -->
      <div class="bm-card p-3 sm:p-4 mb-8 max-w-2xl mx-auto shadow-sm border border-purple-100/60">
        <form @submit.prevent="handleQuickAdd" class="flex items-center gap-2">
          <div class="relative flex-1">
            <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <input 
              v-model="newServerUrl"
              type="text"
              placeholder="Paste server URL and press Enter (e.g. http://127.0.0.1:8000)..."
              class="w-full pl-10 pr-4 py-3 bg-transparent text-sm text-gray-900 placeholder-gray-400 focus:outline-none"
              required
            />
          </div>
          <button 
            type="submit"
            :disabled="!newServerUrl.trim()"
            class="bm-btn-primary px-5 py-3 text-sm shadow flex items-center gap-2 shrink-0 disabled:opacity-50"
          >
            Connect
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        </form>
      </div>

      <!-- Server Cards Section Header -->
      <div class="flex items-center justify-between mb-4 px-1">
        <h2 class="text-sm font-bold uppercase tracking-wider text-gray-700">
          Registered Servers ({{ servers.length }})
        </h2>

        <!-- Save button to modify config file (Issue #11) -->
        <button 
          @click="handleSaveConfig"
          class="text-xs font-semibold px-3 py-1.5 rounded-lg bg-white hover:bg-purple-50 text-[#833dff] border border-purple-200 transition shadow-2xs flex items-center gap-1.5"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
          Save to Config File
        </button>
      </div>

      <!-- Notification banner if saved -->
      <div 
        v-if="toastMessage" 
        class="mb-4 p-3 bg-purple-50 border border-purple-200 rounded-xl text-xs text-purple-900 flex items-center justify-between animate-fade-in"
      >
        <span>✓ {{ toastMessage }}</span>
        <button @click="toastMessage = ''" class="text-purple-600 hover:text-purple-900 font-bold">&times;</button>
      </div>

      <!-- Grid of Registered Server Cards (Issue #4) -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
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

      <!-- Edit Modal (Issue #4) -->
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
    toastMessage.value = `Server '${created.name}' registered successfully!`
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
