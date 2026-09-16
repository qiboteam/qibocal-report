<template>
  <div id="app" class="min-h-screen bg-[#f7f7f7] text-[#000000]">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { fetchServers } from './store.js'

onMounted(() => {
  fetchServers()
})
</script>
