<!--
  What the launcher adds over the dashboard page.

  On the server list: the way back — a single mark, laid out exactly where
  the launcher header puts its own, same column, same height, so stepping
  between the two halves moves nothing on the screen — and the status bar
  the rest of the application speaks from, which that page has room for.
  Every other dashboard page fills those edges with its own interface, and
  gets a bell in its toolbar instead. The closing dialog is for all of them.
-->
<template>
  <div v-if="onServers" class="lx-overlay">
    <div class="max-w-5xl mx-auto px-5 h-14 flex items-center">
      <button
        type="button"
        class="lx-logo"
        title="Back to the launcher"
        aria-label="Back to the launcher"
        @click="back"
      >
        <launcher-logo />
      </button>
    </div>
  </div>
  <status-bar v-if="onServers" />
  <shortcuts-dialog />
  <closing-dialog />
</template>

<script setup>
import { computed, inject } from 'vue'
import ClosingDialog from './ClosingDialog.vue'
import LauncherLogo from './LauncherLogo.vue'
import ShortcutsDialog from './ShortcutsDialog.vue'
import StatusBar from './StatusBar.vue'

// The dashboard router's current route, handed over by `dashboard.js`: the
// overlay is a second application on the same page, not a second router.
const route = inject('dashboardRoute', null)

const onServers = computed(() => route?.value?.path === '/servers')

/**
 * Leave the dashboard page for the launcher one. Both are plain pages of the
 * same bundle, so this is an ordinary navigation, not a window change.
 */
function back() {
  const target = new URL('index.html', window.location.href)
  target.hash = '#/'
  window.location.href = target.href
}
</script>
