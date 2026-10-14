<template>
  <div class="max-w-5xl mx-auto px-5 py-8">
    <div class="mb-5">
      <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Running</h1>
      <p class="mt-1 text-xs text-gray-500">
        Everything the launcher started, with its output. Stopping is graceful: sessions get the
        chance to close their tunnels first.
      </p>
    </div>

    <div v-if="!state.processes.length" class="bm-card p-6 text-center">
      <p class="text-xs text-gray-500">Nothing is running yet.</p>
      <div class="mt-3 flex items-center justify-center gap-2">
        <router-link to="/servers" class="lx-action">Start a server</router-link>
        <router-link to="/notebooks" class="lx-action">Open a notebook</router-link>
      </div>
    </div>

    <!-- minmax(0, 1fr): the output column may shrink below its content, which wraps. -->
    <div v-else class="grid gap-4 lg:grid-cols-[18rem_minmax(0,1fr)] items-start">
      <aside class="space-y-2 min-w-0">
        <button
          v-for="process in ordered"
          :key="process.id"
          type="button"
          class="bm-card w-full text-left p-3 transition"
          :class="process.id === selected ? 'ring-2 ring-[#833dff]/30' : ''"
          @click="select(process.id)"
        >
          <div class="flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="dot(process.status)" />
            <span class="text-xs font-medium text-gray-900 truncate flex-1">{{ process.label }}</span>
            <span class="text-[10px] uppercase tracking-wide text-gray-400">{{ process.kind }}</span>
          </div>
          <p class="mt-0.5 lx-mono text-gray-500 truncate">{{ process.detail }}</p>
          <p class="mt-0.5 text-[11px] text-gray-400">{{ statusLabel(process) }}</p>
        </button>
      </aside>

      <section v-if="current" class="bm-card p-4 flex flex-col min-w-0" style="min-height: 26rem">
        <header class="flex flex-wrap items-center gap-2 mb-3">
          <div class="min-w-0 flex-1 basis-64">
            <h2 class="text-sm font-medium text-gray-900 truncate">{{ current.label }}</h2>
            <code class="lx-mono text-gray-400 truncate block" :title="current.command.join(' ')">{{ current.command.join(' ') }}</code>
          </div>
          <div class="ml-auto flex items-center gap-1.5 shrink-0">
            <button v-if="current.url" type="button" class="lx-action" @click="openDashboard(current.url)">
              <LayoutDashboard class="w-3.5 h-3.5" /> Dashboard
            </button>
            <button v-if="current.url" type="button" class="lx-action" @click="openExternal(current.url)">
              <ExternalLink class="w-3.5 h-3.5" /> Browser
            </button>
            <button
              v-if="current.status === 'running' || current.status === 'stopping'"
              type="button"
              class="lx-action"
              :disabled="current.status === 'stopping'"
              @click="stop(current)"
            >
              <Square class="w-3.5 h-3.5" /> {{ current.status === 'stopping' ? 'Stopping…' : 'Stop' }}
            </button>
            <button v-else type="button" class="lx-action" @click="forget(current)">
              <Trash2 class="w-3.5 h-3.5" /> Clear
            </button>
          </div>
        </header>

        <ansi-output
          :text="logText"
          :active="current.status === 'running'"
          :label="`Output of ${current.label}`"
          placeholder="Waiting for output…"
        />
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ExternalLink, LayoutDashboard, Square, Trash2 } from 'lucide-vue-next'
import AnsiOutput from '@dashboard/components/diagnostics/AnsiOutput.vue'
import { desktop, openExternal } from '../bridge.js'
import { state, attempt, loadLog, openDashboard, refreshProcesses } from '../state.js'

const selected = ref(null)

const ordered = computed(() =>
  [...state.processes].sort((left, right) => {
    const running = Number(right.status === 'running') - Number(left.status === 'running')
    return running || right.startedAt - left.startedAt
  })
)
const current = computed(() => state.processes.find(process => process.id === selected.value) || null)
const logText = computed(() => (state.logs[selected.value] || []).join('\n'))

function dot(status) {
  if (status === 'running') return 'bg-emerald-500'
  if (status === 'stopping') return 'bg-amber-500'
  if (status === 'failed') return 'bg-red-500'
  return 'bg-gray-300'
}

function statusLabel(process) {
  if (process.status === 'running') return `running since ${new Date(process.startedAt).toLocaleTimeString()}`
  if (process.status === 'stopping') return 'stopping…'
  if (process.exitCode === null || process.exitCode === undefined) return process.status
  return `${process.status} (code ${process.exitCode})`
}

async function select(id) {
  selected.value = id
  if (!state.logs[id]) await loadLog(id)
}

async function stop(process) {
  await attempt(() => desktop.stopProcess(process.id))
}

async function forget(process) {
  await attempt(() => desktop.forgetProcess(process.id))
  state.processes = state.processes.filter(entry => entry.id !== process.id)
  delete state.logs[process.id]
  if (selected.value === process.id) selected.value = ordered.value[0]?.id || null
}

onMounted(async () => {
  await refreshProcesses()
  if (!selected.value && ordered.value.length) await select(ordered.value[0].id)
})

watch(ordered, async list => {
  if (!selected.value && list.length) await select(list[0].id)
})
</script>
