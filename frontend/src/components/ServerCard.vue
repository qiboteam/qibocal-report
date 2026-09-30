<template>
  <div
    @click="handleClick"
    class="bm-card border-0 p-4.5 cursor-pointer relative group flex flex-col justify-between transition-all duration-50"
    :class="isActive ? 'shadow-md bg-purple-50/25' : 'hover:shadow-md'"
  >
    <div>
      <!-- Top row: Avatar, Info, Horizontal 3-dots menu -->
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <!-- Elegant Compact Avatar Icon -->
          <div
            class="w-9 h-9 rounded-lg flex items-center justify-center p-1 bg-[#fcfaff] shadow-2xs shrink-0"
            v-html="renderAvatar(server.avatar, server.name)"
          ></div>

          <div class="min-w-0">
            <div class="flex items-center gap-1.5">
              <h3 class="font-medium text-sm text-gray-900 truncate leading-snug">{{ server.name }}</h3>
              <span
                v-if="isActive"
                class="px-1.5 py-0.2 text-[10px] font-medium bg-[#833dff]/10 text-[#833dff] rounded"
              >
                Active
              </span>
            </div>
            <p class="text-xs font-mono text-gray-400 truncate mt-0.5">{{ server.url }}</p>
          </div>
        </div>

        <!-- Right controls: Drag grip handle + 3-dots menu -->
        <div class="flex items-center gap-0.5 shrink-0" @click.stop>
          <div
            class="w-6 h-6 flex items-center justify-center text-gray-300 hover:text-gray-600 transition-colors rounded cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100"
            title="Drag to swap card position on grid"
          >
            <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M7 2a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 2zm0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 8zm0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 14zm6-12a2 2 0 1 0 .001 4.001A2 2 0 0 0 13 2zm0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 13 8zm0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 13 14z" />
            </svg>
          </div>

          <div class="relative shrink-0">
            <button
              draggable="false"
              @click="menuOpen = !menuOpen"
              class="border-0 w-7 h-7 flex items-center justify-center rounded-md bg-transparent text-gray-400 hover:text-gray-700 hover:shadow-xs transition-shadow focus:outline-none cursor-pointer"
              title="Options"
            >
              <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM18 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </button>

            <!-- Dropdown menu -->
            <div
              v-if="menuOpen"
            class="absolute right-0 mt-1 w-32 bg-white rounded-xl shadow-lg py-1 z-30 animate-fade-in"
          >
            <button
              @click="onAdmin"
              class="border-0 w-full px-3 py-1.5 text-left text-xs text-gray-700 hover:bg-purple-50 hover:text-[#833dff] flex items-center gap-2 bg-transparent"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Administer
            </button>
            <button
              @click="onEdit"
              class="border-0 w-full px-3 py-1.5 text-left text-xs text-gray-700 hover:bg-purple-50 hover:text-[#833dff] flex items-center gap-2 bg-transparent"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
              Edit
            </button>
            <button
              v-if="isAuthenticatedOnServer"
              @click="onLogout"
              class="border-0 w-full px-3 py-1.5 text-left text-xs text-gray-700 hover:bg-purple-50 hover:text-[#833dff] flex items-center gap-2 bg-transparent"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H5a2 2 0 00-2 2v10a2 2 0 002 2h4m7-12l5 5-5 5m5-5H9" />
              </svg>
              Log out
            </button>
            <button
              @click="onDelete"
              class="border-0 w-full px-3 py-1.5 text-left text-xs text-red-600 hover:bg-red-50 flex items-center gap-2 bg-transparent"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>

      <!-- Description -->
      <p class="text-xs text-gray-500 mt-2.5 line-clamp-2 leading-relaxed">
        {{ server.description || 'No description provided.' }}
      </p>
    </div>

    <!-- Bottom row: status and quick action -->
    <div class="mt-3.5 pt-2.5 border-t border-gray-100/50 flex items-center justify-between text-xs">
      <div class="flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full" :class="statusColor"></span>
        <span class="text-[11px] text-gray-400 font-medium">{{ statusLabel }}</span>
        <button
          v-if="connectionStatus === 'disconnected' && !isChecking"
          @click.stop="retryConnection"
          class="text-[10px] font-medium text-blue-700 bg-blue-50 border border-blue-200/60 px-1.5 py-0.2 rounded ml-1 hover:bg-blue-100 transition-colors cursor-pointer border-0 bg-transparent text-blue-600 hover:text-blue-700"
          title="Retry connection"
        >
          Retry
        </button>
        <span v-if="isChecking" class="text-[10px] text-gray-400 ml-1">
          <svg class="w-3 h-3 inline animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </span>
        <span v-if="reportCount !== null && reportCount > 0" class="text-[10px] text-gray-500 bg-gray-100 font-mono px-1.5 py-0.2 rounded ml-1">
          {{ reportCount }} runs
        </span>
        <span
          v-if="requiresAuth && !isAuthenticatedOnServer"
          class="text-[10px] font-medium text-amber-700 bg-amber-50 border border-amber-200/60 px-1.5 py-0.2 rounded ml-1 flex items-center gap-1"
        >
          <svg class="w-2.5 h-2.5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          Auth Required
        </span>
      </div>
      <span class="text-[11px] font-medium text-gray-400 group-hover:text-[#833dff] flex items-center gap-1 transition-colors">
        {{ requiresAuth && !isAuthenticatedOnServer ? 'Sign in' : 'Browse' }}
        <svg class="w-3 h-3 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { renderAvatar } from './Avatars.js'
import { state, normalizeUrl, getActiveAuthToken } from '../store.js'

const props = defineProps({
  server: { type: Object, required: true },
  isActive: { type: Boolean, default: false }
})

const emit = defineEmits(['select', 'edit', 'delete', 'administer', 'logout'])

const menuOpen = ref(false)
const reportCount = ref(null)
const checkedRequiresAuth = ref(false)
const requiresAuth = computed(() => props.isActive && state.auth.checked
  ? state.auth.enabled
  : checkedRequiresAuth.value)
const isAuthenticatedOnServer = computed(() => Boolean(getActiveAuthToken(props.server)))
const isChecking = ref(false)
let checkHealthTimeout = null
let pendingAction = null

// Store connection status in localStorage
function getStorageKey() {
  return `server_connection_${props.server?.id || normalizeUrl(props.server?.url)}`
}

function getStoredStatus() {
  try {
    const key = getStorageKey()
    const stored = localStorage.getItem(key)
    return stored || 'unchecked'
  } catch {
    return 'unchecked'
  }
}

function saveStatus(status) {
  try {
    const key = getStorageKey()
    localStorage.setItem(key, status)
  } catch {
    // Silently fail if localStorage not available
  }
}

const connectionStatus = ref(getStoredStatus())

const statusLabel = computed(() => {
  switch (connectionStatus.value) {
    case 'online':
      return 'Online'
    case 'disconnected':
      return 'Disconnected'
    case 'checking':
      return 'Checking...'
    default:
      return 'Disconnected'
  }
})

const statusColor = computed(() => {
  switch (connectionStatus.value) {
    case 'online':
      return 'bg-emerald-500'
    case 'disconnected':
      return 'bg-red-400'
    case 'checking':
      return 'bg-yellow-400'
    default:
      return 'bg-gray-300'
  }
})

function closeMenu(e) {
  if (menuOpen.value) menuOpen.value = false
}

onMounted(() => {
  window.addEventListener('click', closeMenu)
})

watch(() => props.server?.url, () => {
  // Don't auto-check on URL change, wait for user interaction
})

onUnmounted(() => {
  window.removeEventListener('click', closeMenu)
  if (checkHealthTimeout) clearTimeout(checkHealthTimeout)
})

async function checkHealth() {
  if (isChecking.value) return
  
  isChecking.value = true
  connectionStatus.value = 'checking'
  
  if (checkHealthTimeout) clearTimeout(checkHealthTimeout)
  
  // Set a timeout to mark as disconnected after 10 seconds
  checkHealthTimeout = setTimeout(() => {
    if (connectionStatus.value === 'checking') {
      connectionStatus.value = 'disconnected'
      saveStatus('disconnected')
      isChecking.value = false
      executePendingAction()
    }
  }, 10000)

  try {
    const normalized = normalizeUrl(props.server?.url)
    const targetUrl = normalized ? `${normalized}/api/health` : '/api/health'
    const statusUrl = normalized ? `${normalized}/api/auth/status` : '/api/auth/status'

    const [hRes, aRes] = await Promise.all([
      fetch(targetUrl, { signal: AbortSignal.timeout(5000), cache: 'no-store' }).catch(() => null),
      fetch(statusUrl, { signal: AbortSignal.timeout(5000), cache: 'no-store' }).catch(() => null)
    ])

    if (checkHealthTimeout) clearTimeout(checkHealthTimeout)

    if (hRes && hRes.ok) {
      const data = await hRes.json()
      connectionStatus.value = 'online'
      saveStatus('online')
      reportCount.value = data.reports_count
    } else {
      connectionStatus.value = 'disconnected'
      saveStatus('disconnected')
      reportCount.value = null
    }

    if (aRes && aRes.ok) {
      const authData = await aRes.json()
      checkedRequiresAuth.value = Boolean(authData.auth_enabled)
    }
  } catch {
    if (checkHealthTimeout) clearTimeout(checkHealthTimeout)
    connectionStatus.value = 'disconnected'
    saveStatus('disconnected')
    reportCount.value = null
  } finally {
    isChecking.value = false
    executePendingAction()
  }
}

function executePendingAction() {
  if (!pendingAction) return
  
  const action = pendingAction
  pendingAction = null
  
  // Only execute if we're now online
  if (connectionStatus.value === 'online') {
    action()
  }
}

function retryConnection() {
  checkHealth()
}

function handleClick() {
  // If not yet checked or disconnected, try to connect first
  if (connectionStatus.value === 'unchecked' || connectionStatus.value === 'disconnected') {
    pendingAction = () => {
      emit('select', props.server)
    }
    checkHealth()
    return
  }
  
  // If still checking, wait
  if (connectionStatus.value === 'checking') {
    return
  }
  
  emit('select', props.server)
}

function onLogout() {
  menuOpen.value = false
  emit('logout', props.server)
}

function onAdmin() {
  menuOpen.value = false
  
  // Administer requires a connection
  if (connectionStatus.value === 'disconnected' || connectionStatus.value === 'unchecked') {
    pendingAction = () => {
      emit('administer', props.server)
    }
    checkHealth()
    return
  }
  
  if (connectionStatus.value === 'checking') {
    return
  }
  
  emit('administer', props.server)
}

function onEdit() {
  menuOpen.value = false
  // Edit doesn't require connection
  emit('edit', props.server)
}

function onDelete() {
  menuOpen.value = false
  // Delete doesn't require connection
  emit('delete', props.server)
}
</script>
