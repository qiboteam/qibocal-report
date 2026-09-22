<template>
  <div class="spinner-showcase p-8">
    <h1 class="text-2xl font-bold mb-8 text-center">Loading Spinners Showcase</h1>
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-8">
      <div class="spinner-card">
        <p class="spinner-name">Atom</p>
        <div class="spinner-demo">
          <AtomSpinner />
        </div>
      </div>
      <div class="spinner-card">
        <p class="spinner-name">Wave</p>
        <div class="spinner-demo">
          <WaveSpinner />
        </div>
      </div>
      <div class="spinner-card">
        <p class="spinner-name">Pulse</p>
        <div class="spinner-demo">
          <PulseSpinner />
        </div>
      </div>
      <div class="spinner-card">
        <p class="spinner-name">Orbit</p>
        <div class="spinner-demo">
          <OrbitSpinner />
        </div>
      </div>
      <div class="spinner-card">
        <p class="spinner-name">Tunnel</p>
        <div class="spinner-demo">
          <TunnelSpinner />
        </div>
      </div>
    </div>
    <div class="mt-12 text-center">
      <p class="text-sm text-gray-600 mb-4">Random Selection Demo (refresh to see different spinners)</p>
      <LoadingSpinner label="Loading..." />
    </div>
  </div>
</template>

<script setup>
import LoadingSpinner from './LoadingSpinner.vue'
import AtomSpinner from './spinners/AtomSpinner.vue'
import WaveSpinner from './spinners/WaveSpinner.vue'
import PulseSpinner from './spinners/PulseSpinner.vue'
import OrbitSpinner from './spinners/OrbitSpinner.vue'
import TunnelSpinner from './spinners/TunnelSpinner.vue'
</script>

<style scoped>
.spinner-showcase {
  background: #f7f7f7;
  min-height: 100vh;
}

.spinner-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 2px 8px rgba(131, 61, 255, 0.03);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  min-height: 180px;
}

.spinner-name {
  font-weight: 600;
  color: #833dff;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 1rem;
}

.spinner-demo {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
}
</style>

