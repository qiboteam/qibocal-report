<template>
  <div class="loading-spinner-container">
    <div class="spinner-wrapper">
      <AtomSpinner v-if="spinnerType === 'atom'" />
      <WaveSpinner v-else-if="spinnerType === 'wave'" />
      <PulseSpinner v-else-if="spinnerType === 'pulse'" />
      <OrbitSpinner v-else-if="spinnerType === 'orbit'" />
      <TunnelSpinner v-else-if="spinnerType === 'tunnel'" />
    </div>
    <p v-if="label" class="loading-label">{{ label }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AtomSpinner from './spinners/AtomSpinner.vue'
import WaveSpinner from './spinners/WaveSpinner.vue'
import PulseSpinner from './spinners/PulseSpinner.vue'
import OrbitSpinner from './spinners/OrbitSpinner.vue'
import TunnelSpinner from './spinners/TunnelSpinner.vue'

const props = defineProps({
  label: {
    type: String,
    default: null
  }
})

const spinnerType = ref('atom')

const spinnerTypes = ['atom', 'wave', 'pulse', 'orbit', 'tunnel']

onMounted(() => {
  spinnerType.value = spinnerTypes[Math.floor(Math.random() * spinnerTypes.length)]
})
</script>

<style scoped>
.loading-spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  min-height: 100px;
}

.spinner-wrapper {
  position: relative;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-label {
  margin-top: 1.5rem;
  color: var(--accent-primary);
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: 0.5px;
}
</style>

