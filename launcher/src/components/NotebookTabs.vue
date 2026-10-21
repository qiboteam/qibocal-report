<!--
  The two pages of Notebooks: the sessions, and the remote execution
  connections a session can hand its acquisitions to — distinct things,
  linked by a session's "Remote execution", so kept side by side.
-->
<template>
  <nav class="flex gap-1.5" aria-label="Notebooks pages">
    <router-link
      v-for="tab in tabs"
      :key="tab.name"
      :to="{ name: tab.name }"
      class="px-3 py-1.5 rounded-xl text-xs font-semibold transition"
      :class="route.name === tab.name ? 'bg-[#ebe0ff] text-[#3b107e]' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'"
    >{{ tab.label }} <span class="ml-1 font-normal text-gray-400">{{ tab.count() }}</span></router-link>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { state } from '../state.js'

const route = useRoute()
const tabs = [
  { name: 'notebooks', label: 'Sessions', count: () => Object.keys(state.notebooks || {}).length },
  { name: 'remotes', label: 'Remote execution', count: () => Object.keys(state.remotes || {}).length }
]
</script>
