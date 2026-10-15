<!--
  A labelled control, with the conventions the forms share.

  A required field says so next to its label, and its control is drawn
  white and outlined, where an optional one stays grey; `help` is one brief
  line under the control, and `info` the longer explanation behind the
  circled i. The slot receives the identifier the label points at, and the
  class that marks a required control.
-->
<template>
  <div>
    <span class="lx-label-row">
      <label class="lx-label" :for="id">{{ label }}</label>
      <span v-if="required" class="lx-tag">required</span>
      <info-tip v-if="info" :text="info" />
    </span>
    <slot :id="id" :control="required ? 'is-required' : ''" />
    <p v-if="error" class="lx-error">{{ error }}</p>
    <p v-else-if="warning" class="lx-warning">{{ warning }}</p>
    <p v-else-if="help" class="lx-help">{{ help }}</p>
  </div>
</template>

<script setup>
import InfoTip from './InfoTip.vue'

defineProps({
  label: { type: String, required: true },
  help: { type: String, default: '' },
  info: { type: String, default: '' },
  required: { type: Boolean, default: false },
  error: { type: String, default: '' },
  warning: { type: String, default: '' }
})

// Each instance gets its own identifier, so the label points at its control.
const id = `lx-${Math.random().toString(36).slice(2, 9)}`
</script>
