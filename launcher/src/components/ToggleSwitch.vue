<template>
  <button
    type="button"
    role="switch"
    :aria-checked="modelValue"
    class="flex items-center gap-2.5 text-left"
    @click="$emit('update:modelValue', !modelValue)"
  >
    <span class="lx-switch" :class="{ 'is-on': modelValue }" />
    <span>
      <span class="block text-xs font-medium text-gray-800">{{ label }}</span>
      <span v-if="help" class="block lx-help !mt-0">{{ help }}</span>
    </span>
  </button>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  label: { type: String, required: true },
  help: { type: String, default: '' }
})
defineEmits(['update:modelValue'])
</script>
