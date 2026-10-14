<!--
  The circled i: a short explanation kept out of the way until asked for.

  Always-visible text under a field is for one line; anything longer goes
  here, shown on hover or focus and readable by assistive technology through
  the button's label.
-->
<template>
  <span class="lx-tip">
    <button type="button" class="lx-tip-button" :aria-label="text">
      <Info class="w-3.5 h-3.5" />
    </button>
    <span class="lx-tip-bubble" role="tooltip">{{ text }}</span>
  </span>
</template>

<script setup>
import { Info } from 'lucide-vue-next'

defineProps({
  text: { type: String, required: true }
})
</script>
