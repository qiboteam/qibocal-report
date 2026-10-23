<!--
  What the launcher shows while it closes with something still running.

  Quitting — the menu, Cmd/Ctrl+Q, the tray — tells every server and session
  to stop and waits: sessions get the moment they need to close their
  tunnels. The dialog lists them, each with a wheel until it is gone, and
  offers to go without waiting — which is also what quitting a second time
  does. The launcher exits by itself when the last one has stopped. Closing
  a window stops nothing: the last one hides, and the launcher stays.
-->
<template>
  <div v-if="state.closing" class="lx-veil" role="dialog" aria-modal="true" aria-labelledby="lx-closing-title">
    <div class="lx-dialog">
      <h2 id="lx-closing-title" class="text-sm font-semibold text-gray-900">Closing Qibocamp</h2>
      <p class="mt-1 text-xs text-gray-500">
        What the launcher started is being stopped; sessions get a moment to close their tunnels. The
        application closes by itself once everything has stopped.
      </p>

      <div class="mt-3">
        <div v-for="process in waited" :key="process.id" class="lx-dialog-row">
          <Loader2 v-if="alive(process)" class="w-3.5 h-3.5 lx-spin text-[#833dff] shrink-0" />
          <Check v-else class="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span class="min-w-0 flex-1">
            <span class="block text-xs font-medium text-gray-900 truncate">{{ process.label }}</span>
            <span class="block lx-mono text-gray-500 truncate">{{ process.detail }}</span>
          </span>
          <span class="text-[11px] text-gray-400 shrink-0">{{ alive(process) ? 'stopping…' : 'stopped' }}</span>
        </div>
      </div>

      <div class="mt-4 flex items-center justify-end gap-2">
        <button type="button" class="lx-action is-danger" title="Close now, killing whatever is still running" @click="force">
          <Power class="w-3.5 h-3.5" /> Force close
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Check, Loader2, Power } from 'lucide-vue-next'
import { state, quit } from '../state.js'

/** The processes the launcher waits for, in the order they were started. */
const waited = computed(() => {
  const ids = new Set(state.closing?.ids || [])
  return state.processes.filter(process => ids.has(process.id))
})

function alive(process) {
  return process.status === 'running' || process.status === 'stopping'
}

async function force() {
  try {
    await quit(true)
  } catch {
    // The window is going; nothing to say.
  }
}
</script>
