<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100">
      <div class="flex items-center justify-between pb-3 border-b border-gray-100">
        <div class="flex items-center gap-2 text-gray-900 font-bold text-base">
          <svg class="w-5 h-5 text-[#833dff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          Remove Label from Reports
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 text-lg cursor-pointer">&times;</button>
      </div>

      <div class="mt-4">
        <p class="text-xs text-gray-500 mb-3">
          Select or enter a label to remove from the
          <strong class="text-gray-800">{{ selectedCount }}</strong> selected report(s).
        </p>

        <label class="block text-xs font-semibold text-gray-700 mb-1">Label / Tag to Remove</label>
        <input
          v-model="unlabelText"
          type="text"
          placeholder="Select a tag below or type name..."
          class="w-full box-border text-xs px-3.5 py-2.5 bg-gray-50 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#833dff] focus:bg-white transition shadow-2xs"
          @keyup.enter="onSubmit"
        />

        <!-- Available tags on selected reports -->
        <div v-if="tagsOnSelected?.length" class="mt-3">
          <span class="text-[11px] text-gray-400 font-medium">Tags on selected reports:</span>
          <div class="flex flex-wrap gap-1 mt-1.5 max-h-24 overflow-y-auto">
            <button
              v-for="t in tagsOnSelected"
              :key="t"
              type="button"
              @click="unlabelText = t"
              class="px-2 py-0.5 rounded text-[11px] font-medium font-mono transition cursor-pointer"
              :class="unlabelText === t ? 'bg-[#833dff] text-white' : 'bg-purple-50 hover:bg-purple-100 text-purple-700'"
            >
              {{ t }}
            </button>
          </div>
        </div>

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
          @click="onSubmit"
          :disabled="!unlabelText.trim() || loading"
          class="bm-btn-primary px-4 py-1.5 text-xs shadow-sm flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
        >
          <span v-if="loading" class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          Remove Label
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  selectedCount: { type: Number, default: 0 },
  tagsOnSelected: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null }
})

const emit = defineEmits(['close', 'submit'])
const unlabelText = ref('')

watch(
  () => props.show,
  (val) => {
    if (val) unlabelText.value = ''
  }
)

function onSubmit() {
  if (unlabelText.value.trim() && !props.loading) {
    emit('submit', unlabelText.value.trim())
  }
}
</script>
