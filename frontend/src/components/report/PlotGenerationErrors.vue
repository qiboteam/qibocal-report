<template>
  <div v-if="errors.length" role="alert" class="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900">
    <h3 class="text-xs font-bold">{{ missing ? 'Qibocal is not installed on this server' : 'Some plots could not be generated' }}</h3>
    <p v-for="message in errors" :key="message" class="text-xs mt-1 leading-relaxed">{{ message }}</p>
    <p v-if="missing" class="text-xs mt-2">
      {{ canManageQibocal ? 'Drag the bottom diagnostics handle upward, then select the Qibocal tab to install it and retry plot generation.' : 'Ask a server administrator to install Qibocal, or use pre-cached report outputs.' }}
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { canManageQibocal } from '../../store.js'
import { getPlotGenerationErrors, isQibocalMissing } from '../../utils/plotGeneration.js'

const props = defineProps({
  protocols: { type: Array, default: () => [] }
})
const errors = computed(() => getPlotGenerationErrors(props.protocols))
const missing = computed(() => isQibocalMissing(props.protocols))
</script>
