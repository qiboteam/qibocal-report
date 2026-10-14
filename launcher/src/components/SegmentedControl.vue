<template>
  <div class="lx-segment" role="radiogroup">
    <button
      v-for="option in options"
      :key="String(option.value)"
      type="button"
      role="radio"
      :aria-checked="option.value === modelValue"
      :class="{ 'is-active': option.value === modelValue }"
      :disabled="option.disabled"
      :title="option.help"
      @click="$emit('update:modelValue', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: null, default: null },
  options: { type: Array, required: true }
})
defineEmits(['update:modelValue'])
</script>
