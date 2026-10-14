<template>
  <div class="lx-bar" role="navigation" aria-label="Launcher">
    <button type="button" class="flex items-center gap-1.5 text-xs font-medium text-gray-700 hover:text-[#833dff] transition" @click="back">
      <ArrowLeft class="w-3.5 h-3.5" />
      Launcher
    </button>
    <span class="w-px h-4 bg-gray-200" />
    <button
      v-for="shortcut in shortcuts"
      :key="shortcut.name"
      type="button"
      class="lx-action"
      :title="shortcut.summary"
      @click="back(shortcut.path)"
    >
      {{ shortcut.title }}
    </button>
  </div>
</template>

<script setup>
import { ArrowLeft } from 'lucide-vue-next'
import { sections } from '../router.js'

const shortcuts = sections.filter(section => ['servers', 'processes', 'notebooks'].includes(section.name))

/**
 * Leave the dashboard page for the launcher one. Both are plain pages of the
 * same bundle, so this is an ordinary navigation, not a window change.
 */
function back(path = '/') {
  const target = new URL('index.html', window.location.href)
  target.hash = `#${typeof path === 'string' ? path : '/'}`
  window.location.href = target.href
}
</script>
