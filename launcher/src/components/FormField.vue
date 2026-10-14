<template>
  <div>
    <label class="lx-label" :for="id">{{ label }}</label>
    <slot :id="id" />
    <p v-if="error" class="lx-error">{{ error }}</p>
    <p v-else-if="warning" class="lx-warning">{{ warning }}</p>
    <p v-else-if="help" class="lx-help">{{ help }}</p>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  help: { type: String, default: '' },
  error: { type: String, default: '' },
  warning: { type: String, default: '' }
})

// Each instance gets its own identifier, so the label points at its control.
const id = `lx-${Math.random().toString(36).slice(2, 9)}`
</script>
