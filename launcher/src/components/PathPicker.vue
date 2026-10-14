<template>
  <div class="flex items-center gap-2">
    <input
      :id="id"
      :value="modelValue"
      type="text"
      class="lx-input lx-mono"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <button
      type="button"
      class="shrink-0 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-[#ebe0ff] text-[#3b107e] hover:bg-[#dfceff] transition inline-flex items-center gap-1.5"
      @click="browse"
    >
      <FolderOpen class="w-3.5 h-3.5" />
      Browse
    </button>
  </div>
</template>

<script setup>
import { FolderOpen } from 'lucide-vue-next'
import { chooseDirectory, chooseFile } from '../bridge.js'
import { fail } from '../state.js'

const props = defineProps({
  modelValue: { type: String, default: '' },
  id: { type: String, default: undefined },
  placeholder: { type: String, default: '' },
  title: { type: String, default: 'Choose a location' },
  directory: { type: Boolean, default: true }
})
const emit = defineEmits(['update:modelValue'])

async function browse() {
  try {
    const pick = props.directory ? chooseDirectory : chooseFile
    const selected = await pick(props.title, props.modelValue || null)
    if (selected) emit('update:modelValue', selected)
  } catch (error) {
    fail(error)
  }
}
</script>
