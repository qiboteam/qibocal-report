<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100">
      <div class="flex items-center justify-between pb-3 border-b border-gray-100">
        <div class="flex items-center gap-2 text-red-600 font-bold text-base">
          <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          Confirm Deletion
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 text-lg cursor-pointer">&times;</button>
      </div>

      <div class="mt-4">
        <p class="text-xs text-gray-700 leading-relaxed">
          Are you sure you want to permanently delete
          <strong class="text-red-600">{{ selectedCount }}</strong> report folder{{ selectedCount > 1 ? 's' : '' }} from the server?
        </p>
        <p class="text-[11px] text-gray-400 mt-1">
          This will remove the report directory and all underlying data files. This action cannot be undone.
        </p>

        <div v-if="error" class="mt-3 p-2 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200">
          {{ error }}
        </div>
      </div>

      <div class="mt-6 flex items-center justify-end gap-2">
        <button
          @click="$emit('close')"
          class="px-3.5 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100 rounded-xl transition cursor-pointer"
        >
          Cancel
        </button>
        <button
          @click="$emit('confirm')"
          :disabled="loading"
          class="px-4 py-1.5 text-xs font-semibold text-white bg-red-600 hover:bg-red-700 rounded-xl shadow-sm transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
        >
          <span v-if="loading" class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          Delete {{ selectedCount }} Report{{ selectedCount > 1 ? 's' : '' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, default: false },
  selectedCount: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null }
})

defineEmits(['close', 'confirm'])
</script>
