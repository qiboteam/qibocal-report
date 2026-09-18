<template>
  <div
    v-if="selectedCount > 0"
    class="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-gray-900/95 text-white px-5 py-3 rounded-2xl shadow-2xl backdrop-blur-md flex items-center gap-4 border border-gray-700/50 animate-fade-in"
  >
    <div class="flex items-center gap-2 pr-3 border-r border-gray-700">
      <span class="w-6 h-6 rounded-full bg-[#833dff] text-white flex items-center justify-center font-bold text-xs">
        {{ selectedCount }}
      </span>
      <span class="text-xs font-medium text-gray-300">
        selected
      </span>
    </div>

    <div class="flex items-center gap-2">
      <button
        @click="$emit('open-label')"
        class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-white transition flex items-center gap-1.5 cursor-pointer border border-gray-700"
      >
        <svg class="w-3.5 h-3.5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
        </svg>
        Tag
      </button>

      <button
        @click="$emit('open-unlabel')"
        class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-white transition flex items-center gap-1.5 cursor-pointer border border-gray-700"
      >
        <svg class="w-3.5 h-3.5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        Untag
      </button>

      <button
        @click="$emit('open-author')"
        class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-white transition flex items-center gap-1.5 cursor-pointer border border-gray-700"
      >
        <svg class="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        Change Author
      </button>

      <button
        @click="$emit('open-delete')"
        class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-red-950/80 hover:bg-red-900 text-red-300 transition flex items-center gap-1.5 cursor-pointer border border-red-800/50"
      >
        <svg class="w-3.5 h-3.5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        Delete
      </button>
    </div>

    <button
      @click="$emit('clear-selection')"
      class="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-gray-800 transition ml-1 cursor-pointer"
      title="Clear selection"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
</template>

<script setup>
defineProps({
  selectedCount: {
    type: Number,
    required: true
  }
})

defineEmits([
  'open-label',
  'open-unlabel',
  'open-author',
  'open-delete',
  'clear-selection'
])
</script>
