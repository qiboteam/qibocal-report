<template>
  <div class="p-3 border-b border-gray-100 flex items-center justify-between gap-2 shrink-0">
    <div v-if="!isCollapsed" class="flex-1 min-w-0">
      <!-- Quick Switch between registered servers -->
      <div class="relative">
        <button
          @click="dropdownOpen = !dropdownOpen"
          class="w-full flex items-center justify-between p-2 rounded-xl bg-gray-50 hover:bg-purple-50 text-left transition border border-gray-100"
        >
          <div class="flex items-center gap-2 truncate">
            <div class="w-6 h-6 rounded-md bg-white p-0.5 shrink-0 shadow-xs" v-html="renderAvatar(activeServer?.avatar || 'quantum-ring')"></div>
            <span class="text-xs font-bold text-gray-800 truncate">{{ activeServer?.name || 'Select Server' }}</span>
          </div>
          <svg class="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Dropdown -->
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

    <!-- Collapse / Expand Button -->
    <button
      @click="$emit('toggle-collapse')"
      class="p-2 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition shrink-0"
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
import { renderAvatar } from '../Avatars.js'

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
</script>
