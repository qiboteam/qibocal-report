<template>
  <div
    class="border-b border-gray-100 shrink-0"
    :class="isCollapsed ? 'p-2 flex flex-col items-center gap-1.5' : 'p-3 flex items-center justify-between gap-2'"
  >
    <!-- Expanded Server Switcher -->
    <div v-if="!isCollapsed" class="flex-1 min-w-0">
      <div class="relative">
        <button
          @click="dropdownOpen = !dropdownOpen"
          class="w-full flex items-center justify-between p-2 rounded-xl bg-gray-50 hover:bg-purple-50 text-left transition border border-gray-100 cursor-pointer"
        >
          <div class="flex items-center gap-2 truncate">
            <div class="w-6 h-6 rounded-md bg-white p-0.5 shrink-0 shadow-xs" v-html="renderAvatar(activeServer?.avatar || 'quantum-ring')"></div>
            <div class="truncate">
              <span class="text-xs font-bold text-gray-800 truncate block">{{ activeServer?.name || 'Select Server' }}</span>
              <span v-if="state.auth?.enabled && state.auth?.user" class="text-[10px] text-gray-400 font-medium truncate block">
                {{ state.auth.user.username }} ({{ state.auth.user.role }})
              </span>
            </div>
          </div>
          <svg class="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Dropdown in expanded mode -->
        <div
          v-if="dropdownOpen"
          class="absolute top-full left-0 mt-1 w-full bg-white rounded-xl shadow-xl border border-gray-100 py-1.5 z-50 text-xs"
        >
          <div class="px-3 py-1 font-semibold text-gray-400 uppercase text-[10px]">Registered Servers</div>
          <div
            v-for="s in servers"
            :key="s.id"
            @click="onSelect(s)"
            class="px-3 py-2 hover:bg-purple-50 cursor-pointer flex items-center justify-between gap-2"
            :class="s.id === activeServer?.id ? 'bg-purple-50/60 font-bold text-[#833dff]' : 'text-gray-700'"
          >
            <div class="truncate">
              <div class="truncate">{{ s.name }}</div>
              <div class="text-[10px] font-mono text-gray-400 truncate">{{ s.url }}</div>
            </div>
            <span v-if="s.id === activeServer?.id" class="w-1.5 h-1.5 rounded-full bg-[#833dff] shrink-0"></span>
          </div>

          <!-- Auth status in expanded mode -->
          <div v-if="state.auth?.enabled" class="border-t border-gray-100 mt-1 pt-1.5 px-3 py-1 bg-gray-50/60">
            <div v-if="state.auth?.user" class="flex items-center justify-between">
              <div class="truncate">
                <div class="text-[11px] font-semibold text-gray-800 truncate">{{ state.auth.user.username }}</div>
                <div class="text-[10px] uppercase font-bold text-[#833dff]">{{ state.auth.user.role }}</div>
              </div>
              <button
                @click="handleLogout"
                class="text-[11px] text-red-600 hover:text-red-800 font-medium cursor-pointer border-0 bg-transparent"
              >
                Sign out
              </button>
            </div>
            <div v-else>
              <button
                @click="openLogin"
                class="w-full py-1 text-center font-semibold text-xs text-[#833dff] hover:bg-purple-50 rounded-lg cursor-pointer border-0 bg-transparent"
              >
                Sign In to Server
              </button>
            </div>
          </div>

          <div class="border-t border-gray-100 mt-1 pt-1">
            <router-link
              to="/servers"
              @click="dropdownOpen = false"
              class="px-3 py-1.5 text-[#833dff] hover:bg-purple-50 flex items-center gap-1.5 font-medium block"
            >
              + Manage Servers...
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Collapsed Server Icon Button -->
    <div v-else class="relative">
      <button
        @click="dropdownOpen = !dropdownOpen"
        class="w-9 h-9 rounded-xl bg-gray-50 hover:bg-purple-50 border border-gray-200/80 flex items-center justify-center transition cursor-pointer shadow-2xs"
        :title="`Server: ${activeServer?.name || 'Local Instance'} (${activeServer?.url || 'local'})`"
      >
        <div class="w-6 h-6 rounded-md bg-white p-0.5 shadow-xs" v-html="renderAvatar(activeServer?.avatar || 'quantum-ring')"></div>
      </button>

      <!-- Dropdown in collapsed mode (floating right) -->
      <div
        v-if="dropdownOpen"
        class="absolute left-full top-0 ml-2 w-56 bg-white rounded-xl shadow-xl border border-gray-100 py-1.5 z-50 text-xs"
      >
        <div class="px-3 py-1 font-semibold text-gray-400 uppercase text-[10px]">Registered Servers</div>
        <div
          v-for="s in servers"
          :key="s.id"
          @click="onSelect(s)"
          class="px-3 py-2 hover:bg-purple-50 cursor-pointer flex items-center justify-between gap-2"
          :class="s.id === activeServer?.id ? 'bg-purple-50/60 font-bold text-[#833dff]' : 'text-gray-700'"
        >
          <div class="truncate">
            <div class="truncate font-semibold">{{ s.name }}</div>
            <div class="text-[10px] font-mono text-gray-400 truncate">{{ s.url }}</div>
          </div>
          <span v-if="s.id === activeServer?.id" class="w-1.5 h-1.5 rounded-full bg-[#833dff] shrink-0"></span>
        </div>

        <!-- Auth status in collapsed mode -->
        <div v-if="state.auth?.enabled" class="border-t border-gray-100 mt-1 pt-1.5 px-3 py-1 bg-gray-50/60">
          <div v-if="state.auth?.user" class="flex items-center justify-between">
            <div class="truncate">
              <div class="text-[11px] font-semibold text-gray-800 truncate">{{ state.auth.user.username }}</div>
              <div class="text-[10px] uppercase font-bold text-[#833dff]">{{ state.auth.user.role }}</div>
            </div>
            <button
              @click="handleLogout"
              class="text-[11px] text-red-600 hover:text-red-800 font-medium cursor-pointer border-0 bg-transparent"
            >
              Sign out
            </button>
          </div>
          <div v-else>
            <button
              @click="openLogin"
              class="w-full py-1 text-center font-semibold text-xs text-[#833dff] hover:bg-purple-50 rounded-lg cursor-pointer border-0 bg-transparent"
            >
              Sign In to Server
            </button>
          </div>
        </div>

        <div class="border-t border-gray-100 mt-1 pt-1">
          <router-link
            to="/servers"
            @click="dropdownOpen = false"
            class="px-3 py-1.5 text-[#833dff] hover:bg-purple-50 flex items-center gap-1.5 font-medium block"
          >
            + Manage Servers...
          </router-link>
        </div>
      </div>
    </div>

    <!-- Collapse / Expand Button -->
    <button
      @click="$emit('toggle-collapse')"
      class="rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition shrink-0 cursor-pointer"
      :class="isCollapsed ? 'w-9 h-9 flex items-center justify-center' : 'p-2'"
      :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path v-if="!isCollapsed" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { renderAvatar } from '../Avatars.js'
import { state, logoutActiveServer, isAdmin } from '../../store.js'

const router = useRouter()

defineProps({
  servers: { type: Array, default: () => [] },
  activeServer: { type: Object, default: null },
  isCollapsed: { type: Boolean, default: false }
})

const emit = defineEmits(['toggle-collapse', 'select-server'])
const dropdownOpen = ref(false)

function onSelect(server) {
  dropdownOpen.value = false
  emit('select-server', server)
}

function openLogin() {
  dropdownOpen.value = false
  state.auth.showLoginModal = true
}

function handleLogout() {
  dropdownOpen.value = false
  logoutActiveServer()
  router.push('/servers')
}
</script>
