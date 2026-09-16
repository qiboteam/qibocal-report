<template>
  <div class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 relative border border-gray-100">
      <!-- Header -->
      <div class="flex items-center justify-between pb-4 border-b border-gray-100">
        <h2 class="text-xl font-bold text-gray-900">
          {{ isEdit ? 'Customize Server' : 'Add New Server' }}
        </h2>
        <button 
          @click="$emit('close')"
          class="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="submitForm" class="mt-4 space-y-4">
        <!-- URL Field -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
            Server URL
          </label>
          <input 
            v-model="form.url" 
            type="url" 
            required
            placeholder="http://127.0.0.1:8000"
            class="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#833dff] focus:border-transparent font-mono"
          />
        </div>

        <!-- Name Field -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
            Server Name
          </label>
          <input 
            v-model="form.name" 
            type="text" 
            placeholder="e.g. quantum-curie"
            class="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#833dff] focus:border-transparent"
          />
        </div>

        <!-- Description -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
            Short Description
          </label>
          <textarea 
            v-model="form.description" 
            rows="2"
            placeholder="Lab QPU calibration archive..."
            class="w-full px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#833dff] focus:border-transparent resize-none"
          ></textarea>
        </div>

        <!-- Avatar Selection (Issue #4) -->
        <div>
          <label class="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
            Abstract Avatar Selection
          </label>
          <div class="grid grid-cols-5 gap-2.5">
            <div 
              v-for="key in AVATAR_KEYS" 
              :key="key"
              @click="form.avatar = key"
              class="w-13 h-13 p-1 rounded-xl cursor-pointer border-2 transition flex items-center justify-center bg-gray-50"
              :class="form.avatar === key ? 'border-[#833dff] bg-purple-50 shadow-sm ring-2 ring-[#833dff]/20' : 'border-gray-200 hover:border-purple-300'"
              :title="key"
            >
              <div class="w-10 h-10" v-html="renderAvatar(key)"></div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="pt-4 border-t border-gray-100 flex items-center justify-end gap-3">
          <button 
            type="button" 
            @click="$emit('close')"
            class="px-4 py-2 rounded-xl text-sm font-semibold text-gray-600 hover:bg-gray-100"
          >
            Cancel
          </button>
          <button 
            type="submit" 
            class="px-5 py-2 bm-btn-primary text-sm shadow"
          >
            {{ isEdit ? 'Save Changes' : 'Register Server' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { AVATAR_KEYS, renderAvatar } from './Avatars.js'

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
  emit('save', { ...form })
}
</script>
