<template>
  <div
    v-if="selectedCount > 0"
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
      <button
        @click="$emit('open-label')"
        class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-purple-50/70 hover:bg-purple-100 text-[#833dff] transition flex items-center gap-1.5 cursor-pointer border border-purple-200 shadow-2xs"
      >
        <svg class="w-3.5 h-3.5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
        </svg>
        Tag
      </button>

      <button
        @click="$emit('open-unlabel')"
        class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-purple-50/70 hover:bg-purple-100 text-[#833dff] transition flex items-center gap-1.5 cursor-pointer border border-purple-200 shadow-2xs"
      >
        <svg class="w-3.5 h-3.5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
        Untag
      </button>

      <button
        @click="$emit('open-author')"
        class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-purple-50/70 hover:bg-purple-100 text-[#833dff] transition flex items-center gap-1.5 cursor-pointer border border-purple-200 shadow-2xs"
      >
        <svg class="w-3.5 h-3.5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        Change Author
      </button>

      <button
        @click="$emit('open-delete')"
        class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-red-50 hover:bg-red-100 text-red-600 transition flex items-center gap-1.5 cursor-pointer border border-red-200 shadow-2xs"
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
