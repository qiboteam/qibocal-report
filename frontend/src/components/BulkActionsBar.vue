<template>
  <div
    v-if="selectedCount > 0"
    style="bottom: calc(var(--diagnostics-height, 0px) + 1.5rem)"
    class="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-white text-gray-800 px-5 py-3 rounded-2xl shadow-2xl backdrop-blur-md flex items-center gap-4 border border-[#833dff]/40 animate-fade-in"
  >
    <div class="flex items-center gap-2 pr-3 border-r border-purple-100">
      <span class="w-6 h-6 rounded-full bg-[#833dff] text-white flex items-center justify-center font-bold text-xs">
        {{ selectedCount }}
      </span>
      <span class="text-xs font-semibold text-gray-700">
        selected
      </span>
    </div>

    <div class="flex items-center gap-2">
      <!-- Tag / Untag split dropdown button -->
      <div class="relative inline-flex rounded-xl shadow-2xs" ref="tagDropdownRef">
        <button
          @click="!isViewer && $emit('open-label')"
          :disabled="isViewer"
          class="px-3 py-1.5 rounded-l-xl text-xs font-semibold bg-purple-50/70 text-[#833dff] transition flex items-center gap-1.5 border border-purple-200 border-r-0"
          :class="isViewer ? 'opacity-40 cursor-not-allowed' : 'hover:bg-purple-100 cursor-pointer'"
          :title="isViewer ? 'Viewer role cannot modify reports' : 'Add label to selected reports'"
        >
          <svg class="w-3.5 h-3.5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
          </svg>
          Tag
        </button>
        <button
          @click.stop="!isViewer && (showTagDropdown = !showTagDropdown)"
          :disabled="isViewer"
          class="px-1.5 py-1.5 rounded-r-xl text-xs font-semibold bg-purple-50/70 text-[#833dff] transition flex items-center border border-purple-200"
          :class="isViewer ? 'opacity-40 cursor-not-allowed' : 'hover:bg-purple-100 cursor-pointer'"
          :title="isViewer ? 'Viewer role cannot modify reports' : 'Tag actions menu'"
        >
          <svg class="w-3.5 h-3.5 text-[#833dff] transition-transform duration-150" :class="{ 'rotate-180': showTagDropdown }" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.25a.75.75 0 01-1.06 0L5.21 8.27a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
          </svg>
        </button>

        <div
          v-if="showTagDropdown && !isViewer"
          class="absolute bottom-full mb-2 left-0 w-36 bg-white rounded-xl shadow-xl border border-purple-100 py-1 z-50 animate-fade-in text-xs overflow-hidden"
        >
          <button
            @click="triggerTagAction('open-label')"
            class="w-full text-left px-3 py-1.5 hover:bg-purple-50 flex items-center gap-2 text-gray-700 font-medium transition cursor-pointer"
          >
            <svg class="w-3.5 h-3.5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            Tag...
          </button>
          <button
            @click="triggerTagAction('open-unlabel')"
            class="w-full text-left px-3 py-1.5 hover:bg-purple-50 flex items-center gap-2 text-red-600 font-medium transition cursor-pointer"
          >
            <svg class="w-3.5 h-3.5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Untag...
          </button>
        </div>
      </div>

      <button
        @click="!isViewer && $emit('open-author')"
        :disabled="isViewer"
        class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-purple-50/70 text-[#833dff] transition flex items-center gap-1.5 border border-purple-200 shadow-2xs"
        :class="isViewer ? 'opacity-40 cursor-not-allowed' : 'hover:bg-purple-100 cursor-pointer'"
        :title="isViewer ? 'Viewer role cannot modify reports' : 'Change author for selected reports'"
      >
        <svg class="w-3.5 h-3.5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        Change Author
      </button>

      <!-- Archive button (Issue #2) -->
      <button
        @click="!isViewer && $emit('open-archive')"
        :disabled="isViewer"
        class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-50/70 text-indigo-600 transition flex items-center gap-1.5 border border-indigo-200 shadow-2xs"
        :class="isViewer ? 'opacity-40 cursor-not-allowed' : 'hover:bg-indigo-100 cursor-pointer'"
        :title="isViewer ? 'Viewer role cannot modify reports' : 'Archive selected reports'"
      >
        <svg class="w-3.5 h-3.5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
        </svg>
        Archive
      </button>

      <button
        @click="!isViewer && $emit('open-delete')"
        :disabled="isViewer"
        class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-red-50 text-red-600 transition flex items-center gap-1.5 border border-red-200 shadow-2xs"
        :class="isViewer ? 'opacity-40 cursor-not-allowed' : 'hover:bg-red-100 cursor-pointer'"
        :title="isViewer ? 'Viewer role cannot modify reports' : 'Delete selected reports'"
      >
        <svg class="w-3.5 h-3.5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        Delete
      </button>
    </div>

    <button
      @click="$emit('clear-selection')"
      class="text-gray-400 hover:text-gray-700 p-1.5 rounded-lg hover:bg-gray-100 transition ml-1 cursor-pointer"
      title="Clear selection"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { isViewer } from '../store.js'

defineProps({
  selectedCount: {
    type: Number,
    required: true
  }
})

const emit = defineEmits([
  'open-label',
  'open-unlabel',
  'open-author',
  'open-archive',
  'open-delete',
  'clear-selection'
])

const showTagDropdown = ref(false)
const tagDropdownRef = ref(null)

function triggerTagAction(action) {
  showTagDropdown.value = false
  emit(action)
}

function handleClickOutside(event) {
  if (tagDropdownRef.value && !tagDropdownRef.value.contains(event.target)) {
    showTagDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
