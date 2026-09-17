<template>
  <div class="fixed inset-0 bg-black/25 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
    <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-5 relative border border-black/[0.08]">
      <!-- Header -->
      <div class="flex items-center justify-between pb-3 border-b border-gray-100">
        <h2 class="text-sm font-semibold text-gray-900">
          {{ isEdit ? 'Edit Server Configuration' : 'Add Server Instance' }}
        </h2>
        <button
          @click="$emit('close')"
          class="border-0 w-6 h-6 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="submitForm" class="mt-3.5 space-y-3.5">
        <!-- URL Field -->
        <div>
          <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1">
            Endpoint URL
          </label>
          <input
            v-model="form.url"
            type="text"
            required
            placeholder="http://127.0.0.1:8000"
            class="w-full px-3 py-2 bg-gray-50/70 border border-gray-200 rounded-lg text-xs font-mono text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#833dff]/15 focus:border-[#833dff] transition"
          />
        </div>

        <!-- Name Field -->
        <div>
          <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1">
            Display Name
          </label>
          <input
            v-model="form.name"
            type="text"
            placeholder="e.g. quantum-curie"
            class="w-full px-3 py-2 bg-gray-50/70 border border-gray-200 rounded-lg text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#833dff]/15 focus:border-[#833dff] transition"
          />
        </div>

        <!-- Description -->
        <div>
          <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1">
            Description
          </label>
          <textarea
            v-model="form.description"
            rows="2"
            placeholder="Lab QPU calibration archive..."
            class="w-full px-3 py-2 bg-gray-50/70 border border-gray-200 rounded-lg text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#833dff]/15 focus:border-[#833dff] transition resize-none"
          ></textarea>
        </div>

        <!-- Avatar Selection (Issue #4) -->
        <div>
          <label class="block text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">
            Abstract Icon
          </label>
          <div class="grid grid-cols-5 gap-2">
            <div
              v-for="key in AVATAR_KEYS"
              :key="key"
              @click="form.avatar = key"
              class="w-10 h-10 p-1 rounded-lg cursor-pointer border transition flex items-center justify-center bg-gray-50/50"
              :class="form.avatar === key ? 'border-[#833dff] bg-purple-50/80 ring-2 ring-[#833dff]/20' : 'border-gray-200 hover:border-gray-300'"
              :title="key"
            >
              <div class="w-8 h-8" v-html="renderAvatar(key)"></div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="pt-3 border-t border-gray-100 flex items-center justify-end gap-2">
          <button
            type="button"
            @click="$emit('close')"
            class="border-0 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-100 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="border-0 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-[#833dff] text-white hover:bg-[#722ce6] active:scale-[0.98] transition shadow-2xs"
          >
            {{ isEdit ? 'Save Changes' : 'Register' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { AVATAR_KEYS, renderAvatar } from './Avatars.js'
import { normalizeUrl } from '../store.js'

const props = defineProps({
  server: { type: Object, default: null }
})

const emit = defineEmits(['close', 'save'])

const isEdit = computed(() => !!props.server?.id)

const form = reactive({
  id: props.server?.id || null,
  url: props.server?.url || '',
  name: props.server?.name || '',
  description: props.server?.description || '',
  avatar: props.server?.avatar || 'quantum-ring'
})

function submitForm() {
  emit('save', { ...form, url: normalizeUrl(form.url) })
}
</script>
