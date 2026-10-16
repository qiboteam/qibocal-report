<!--
  The keyboard shortcuts, on `?`, as GitHub shows its own: the page's keys
  first, then the ones that work everywhere. As wide as the columns want, up
  to most of the window, never taller than most of it: the list scrolls under
  its title. Only in a browser — inside the
  desktop launcher the launcher's own cheatsheet lists these.
-->
<template>
  <div
    v-if="cheatsheetOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-[#f7f7f7]/80 backdrop-blur-sm"
    @pointerdown.self="cheatsheetOpen = false"
  >
    <div class="w-[min(56rem,calc(100vw-2.5rem))] max-h-[min(38rem,calc(100vh-4rem))] flex flex-col bg-white rounded-2xl shadow-xl p-6 text-xs" role="dialog" aria-modal="true" aria-labelledby="dashboard-shortcuts-title">
      <div class="flex items-start gap-3 shrink-0">
        <div class="min-w-0">
          <h2 id="dashboard-shortcuts-title" class="text-sm font-semibold text-gray-900">Keyboard shortcuts</h2>
          <p class="mt-0.5 text-gray-500">Letters work anywhere but in a text field.</p>
        </div>
        <button type="button" class="ml-auto shrink-0 text-gray-400 hover:text-gray-700 cursor-pointer" title="Close" @click="cheatsheetOpen = false">&times;</button>
      </div>

      <div class="min-h-0 overflow-y-auto overscroll-contain -mr-2.5 pr-2.5">
        <div v-for="group in groups" :key="group.title" class="mt-4">
          <p class="text-[11px] font-semibold uppercase tracking-wider text-gray-400 mb-2">{{ group.title }}</p>
          <dl class="grid gap-x-6 gap-y-1.5 grid-cols-[repeat(auto-fill,minmax(16rem,1fr))]">
            <div v-for="shortcut in group.entries" :key="shortcut.what" class="flex items-start gap-2">
              <dt class="shrink-0 whitespace-nowrap">
                <kbd
                  v-for="key in shortcut.keys"
                  :key="key"
                  class="inline-block min-w-[1.4em] px-1.5 py-px mr-0.5 rounded border border-gray-200 border-b-2 bg-gray-50 font-mono text-[11px] text-gray-800 text-center"
                >{{ key }}</kbd>
              </dt>
              <dd class="text-gray-700 min-w-0">{{ shortcut.what }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { cheatsheetOpen, currentPage, pageShortcuts } from '../../utils/shortcuts.js'

const groups = computed(() => [pageShortcuts(currentPage.value), pageShortcuts('global')].filter(Boolean))
</script>
