<template>
  <div
    @click="$emit('select', server)"
    class="bm-card border-0 p-4.5 cursor-pointer relative group flex flex-col justify-between transition-all duration-150"
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

        <!-- Horizontal 3-dots menu button -->
        <div class="relative shrink-0" @click.stop>
          <button
            @click="menuOpen = !menuOpen"
            class="border-0 w-7 h-7 flex items-center justify-center rounded-md bg-transparent text-gray-400 hover:text-gray-700 hover:shadow-xs transition-shadow focus:outline-none"
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
              @click="onEdit"
              class="border-0 w-full px-3 py-1.5 text-left text-xs text-gray-700 hover:bg-purple-50 hover:text-[#833dff] flex items-center gap-2 bg-transparent"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
              Edit
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

      <!-- Description -->
      <p class="text-xs text-gray-500 mt-2.5 line-clamp-2 leading-relaxed">
        {{ server.description || 'No description provided.' }}
      </p>
    </div>

    <!-- Bottom row: status and quick action -->
    <div class="mt-3.5 pt-2.5 border-t border-gray-100/50 flex items-center justify-between text-xs">
      <div class="flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full" :class="isOnline ? 'bg-emerald-500' : 'bg-gray-300'"></span>
        <span class="text-[11px] text-gray-400 font-medium">{{ isOnline ? 'Online' : 'Checking...' }}</span>
        <span v-if="reportCount !== null" class="text-[10px] text-gray-500 bg-gray-100 font-mono px-1.5 py-0.2 rounded ml-1">
          {{ reportCount }} runs
        </span>
      </div>
      <span class="text-[11px] font-medium text-gray-400 group-hover:text-[#833dff] flex items-center gap-1 transition-colors">
        Browse
        <svg class="w-3 h-3 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { renderAvatar } from './Avatars.js'

const props = defineProps({
  server: { type: Object, required: true },
  isActive: { type: Boolean, default: false }
})

const emit = defineEmits(['select', 'edit', 'delete'])

const menuOpen = ref(false)
const isOnline = ref(true)
const reportCount = ref(null)

function closeMenu(e) {
  if (menuOpen.value) menuOpen.value = false
}

onMounted(() => {
  window.addEventListener('click', closeMenu)
  checkHealth()
})

onUnmounted(() => {
  window.removeEventListener('click', closeMenu)
})

async function checkHealth() {
  try {
    const res = await fetch('/api/health')
    if (res.ok) {
      const data = await res.json()
      isOnline.value = true
      reportCount.value = data.reports_count
    }
  } catch {
    isOnline.value = false
  }
}

function onEdit() {
  menuOpen.value = false
  emit('edit', props.server)
}

function onDelete() {
  menuOpen.value = false
  emit('delete', props.server)
}
</script>
