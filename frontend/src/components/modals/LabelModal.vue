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
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
          </svg>
          Add Label to Reports
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 text-lg cursor-pointer">&times;</button>
      </div>

      <div class="mt-4">
        <p class="text-xs text-gray-500 mb-3">
          Applying this label will add it to the metadata of the
          <strong class="text-gray-800">{{ selectedCount }}</strong> selected report(s).
        </p>

        <label class="block text-xs font-semibold text-gray-700 mb-1">Label / Tag Name</label>
        <input
          v-model="labelText"
          type="text"
          placeholder="e.g. validated, benchmark, fast..."
          class="w-full text-xs px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#833dff] focus:bg-white transition"
          @keyup.enter="onSubmit"
        />

        <!-- Existing suggestions -->
        <div v-if="existingTags?.length" class="mt-3">
          <span class="text-[11px] text-gray-400 font-medium">Existing tags:</span>
          <div class="flex flex-wrap gap-1 mt-1.5 max-h-20 overflow-y-auto">
            <button
              v-for="t in existingTags"
              :key="t"
              type="button"
              @click="labelText = t"
              class="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 hover:bg-purple-100 text-purple-700 font-mono transition cursor-pointer"
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
          :disabled="!labelText.trim() || loading"
          class="bm-btn-primary px-4 py-1.5 text-xs shadow-sm flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
        >
          <span v-if="loading" class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          Apply Label
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
  existingTags: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null }
})

const emit = defineEmits(['close', 'submit'])
const labelText = ref('')

watch(
  () => props.show,
  (val) => {
    if (val) labelText.value = ''
  }
)

function onSubmit() {
  if (labelText.value.trim() && !props.loading) {
    emit('submit', labelText.value.trim())
  }
}
</script>
