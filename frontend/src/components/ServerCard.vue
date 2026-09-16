<template>
  <div 
    @click="$emit('select', server)"
    class="bm-card p-5 cursor-pointer relative group flex flex-col justify-between border-2 transition-all duration-200"
    :class="isActive ? 'border-[#833dff] shadow-md bg-purple-50/20' : 'border-transparent hover:border-purple-200'"
  >
    <div>
      <!-- Top row: Avatar, Info, 3-dots menu -->
      <div class="flex items-start justify-between gap-4">
        <div class="flex items-center gap-3.5">
          <!-- Avatar Icon -->
          <div 
            class="w-13 h-13 rounded-xl flex items-center justify-center p-1.5 shadow-sm bg-white shrink-0"
            v-html="renderAvatar(server.avatar, server.name)"
          ></div>

          <div>
            <div class="flex items-center gap-2">
              <h3 class="font-bold text-base text-gray-900 leading-snug">{{ server.name }}</h3>
              <span 
                v-if="isActive" 
                class="px-2 py-0.5 text-xs font-semibold bg-[#833dff] text-white rounded-full"
              >
                Active
              </span>
            </div>
            <p class="text-xs font-mono text-gray-500 truncate max-w-xs mt-0.5">{{ server.url }}</p>
          </div>
        </div>

        <!-- 3-dots menu button -->
        <div class="relative" @click.stop>
          <button 
            @click="menuOpen = !menuOpen"
            class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-700 transition"
            title="Options"
          >
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
            </svg>
          </button>

          <!-- Dropdown menu -->
          <div 
            v-if="menuOpen" 
            class="absolute right-0 mt-1 w-36 bg-white rounded-xl shadow-lg border border-gray-100 py-1.5 z-20"
          >
            <button 
              @click="onEdit"
              class="w-full px-3.5 py-1.5 text-left text-sm text-gray-700 hover:bg-purple-50 hover:text-[#833dff] flex items-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
              Edit
            </button>
            <button 
              @click="onDelete"
              class="w-full px-3.5 py-1.5 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete
            </button>
          </div>
        </div>
      </div>

      <!-- Description -->
      <p class="text-sm text-gray-600 mt-3 line-clamp-2">
        {{ server.description || 'No description provided.' }}
      </p>
    </div>

    <!-- Bottom row: status and quick action -->
    <div class="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
      <div class="flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full" :class="isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'"></span>
        <span class="text-gray-500 font-medium">{{ isOnline ? 'Online' : 'Checking...' }}</span>
        <span v-if="reportCount !== null" class="text-purple-700 bg-purple-100 font-semibold px-2 py-0.5 rounded-full ml-1">
          {{ reportCount }} reports
        </span>
      </div>
      <span class="text-[#833dff] font-semibold group-hover:underline flex items-center gap-1">
        Browse Reports
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
