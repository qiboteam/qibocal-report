<!--
  The keyboard shortcuts, on `?`, as GitHub shows its own: a card over the
  page, gone on Escape or a click outside. Wide enough for the columns the
  window allows, never taller than most of it: the title and the way to Help
  stay put, and the list scrolls between them. The Help page has the same
  list, with the rest of the guide.
-->
<template>
  <div v-if="state.cheatsheet" class="lx-veil" @pointerdown.self="state.cheatsheet = false">
    <div class="lx-dialog lx-dialog-sheet" role="dialog" aria-modal="true" aria-labelledby="lx-shortcuts-title">
      <div class="flex items-start gap-3 shrink-0">
        <div class="min-w-0">
          <h2 id="lx-shortcuts-title" class="text-sm font-semibold text-gray-900">Keyboard shortcuts</h2>
          <p class="mt-0.5 text-xs text-gray-500">Letters work anywhere but in a text field; the menu shortcuts work everywhere.</p>
        </div>
        <button type="button" class="lx-action ml-auto shrink-0" title="Close" @click="state.cheatsheet = false">
          <X class="w-3.5 h-3.5" />
        </button>
      </div>

      <div class="lx-dialog-scroll mt-4">
        <!-- What the keys mean here, on this page, before what they mean everywhere. -->
        <div v-if="state.pageShortcuts" class="rounded-xl bg-[#f7f5ff] px-3.5 py-3 mb-4">
          <p class="text-[11px] font-semibold uppercase tracking-wider text-[#3b107e] mb-2">On this page · {{ state.pageShortcuts.title }}</p>
          <dl class="lx-shortcut-columns gap-y-1.5">
            <div v-for="shortcut in state.pageShortcuts.entries" :key="shortcut.what" class="flex items-start gap-2 text-xs">
              <dt class="shrink-0 whitespace-nowrap">
                <kbd v-for="key in describeKeys(shortcut.keys)" :key="key" class="lx-kbd">{{ key }}</kbd>
              </dt>
              <dd class="text-gray-700 min-w-0">{{ shortcut.what }}</dd>
            </div>
          </dl>
        </div>

        <div class="lx-shortcut-columns gap-y-4">
          <div v-for="group in groups" :key="group.name">
            <p class="text-[11px] font-semibold uppercase tracking-wider text-gray-400 mb-2">{{ group.name }}</p>
            <dl class="space-y-1.5">
              <div v-for="shortcut in group.entries" :key="shortcut.what" class="flex items-start gap-2 text-xs">
                <dt class="shrink-0 whitespace-nowrap">
                  <kbd v-for="key in describeKeys(shortcut.keys)" :key="key" class="lx-kbd">{{ key }}</kbd>
                </dt>
                <dd class="text-gray-700 min-w-0">{{ shortcut.what }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      <p class="mt-3 pt-3 border-t border-gray-100 text-[11px] text-gray-400 shrink-0">
        The whole guide is in
        <a :href="launcherHref({ name: 'help' })" class="text-[#833dff] hover:text-[#3b107e]" @click="state.cheatsheet = false">Help</a>.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { X } from 'lucide-vue-next'
import { state } from '../state.js'
import { SHORTCUTS, describeKeys } from '../shortcuts.js'
import { launcherHref } from '../lib/links.js'

const groups = computed(() => {
  const byName = new Map()
  for (const shortcut of SHORTCUTS) {
    if (!byName.has(shortcut.group)) byName.set(shortcut.group, { name: shortcut.group, entries: [] })
    byName.get(shortcut.group).entries.push(shortcut)
  }
  return [...byName.values()]
})
</script>
