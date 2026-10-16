<template>
  <div class="max-w-5xl mx-auto px-5 py-8">
    <div class="mb-5">
      <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Running</h1>
      <p class="mt-1 text-xs text-gray-500">
        Everything the launcher started, one card per server or session, with every run since the
        application was opened. Stopping is graceful: sessions get the chance to close their tunnels first.
      </p>
    </div>

    <div v-if="!groups.length" class="bm-card p-6 text-center">
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
          v-for="group in groups"
          :key="group.key"
          type="button"
          class="bm-card w-full text-left p-3 transition"
          :class="group.key === selected ? 'ring-2 ring-[#833dff]/30' : ''"
          @click="select(group.key)"
        >
          <div class="flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="dot(group.latest.status)" />
            <span class="text-xs font-medium text-gray-900 truncate flex-1">{{ group.latest.label }}</span>
            <span class="text-[10px] uppercase tracking-wide text-gray-400">{{ group.latest.kind }}</span>
          </div>
          <p class="mt-0.5 lx-mono text-gray-500 truncate">{{ group.latest.detail }}</p>
          <p class="mt-0.5 text-[11px] text-gray-400">
            {{ statusLabel(group.latest) }}<template v-if="group.runs.length > 1"> · {{ group.runs.length }} runs</template>
          </p>
        </button>
      </aside>

      <section v-if="current" class="bm-card p-4 flex flex-col min-w-0 gap-3">
        <header class="flex flex-wrap items-center gap-2">
          <div class="min-w-0 flex-1 basis-64">
            <h2 class="text-sm font-medium text-gray-900 truncate">{{ current.latest.label }}</h2>
            <code class="lx-mono text-gray-400 truncate block" :title="current.latest.command.join(' ')">{{ current.latest.command.join(' ') }}</code>
          </div>
          <div class="ml-auto flex items-center gap-1.5 shrink-0">
            <!-- A server is read in the embedded dashboard, a notebook in the browser. -->
            <button
              v-if="current.latest.url && current.latest.kind === 'server' && current.latest.status === 'running'"
              type="button"
              class="lx-action"
              title="Open it in the dashboard, registering it if it is not yet"
              @click="openDashboard(current.latest.url, { newWindow: wantsNewWindow($event) })"
              @auxclick.prevent="$event.button === 1 && openDashboard(current.latest.url, { newWindow: true })"
            >
              <LayoutDashboard class="w-3.5 h-3.5" /> Dashboard
            </button>
            <button
              v-if="current.latest.url && current.latest.kind === 'notebook' && current.latest.status === 'running'"
              type="button"
              class="lx-action"
              @click="openExternal(current.latest.url)"
            >
              <ExternalLink class="w-3.5 h-3.5" /> Browser
            </button>
            <button
              v-if="current.latest.status === 'running' || current.latest.status === 'stopping'"
              type="button"
              class="lx-action"
              :disabled="current.latest.status === 'stopping'"
              @click="stop(current.latest)"
            >
              <Square class="w-3.5 h-3.5" /> {{ current.latest.status === 'stopping' ? 'Stopping…' : 'Stop' }}
            </button>
            <template v-else>
              <!-- Stopped: start it again as it was, and the new run joins this card. -->
              <button
                v-if="canRestart(current.latest)"
                type="button"
                class="lx-primary !py-1"
                :disabled="restarting"
                title="Start it again with the same options"
                @click="restart(current.latest)"
              >
                <Play class="w-3.5 h-3.5" /> {{ restarting ? 'Starting…' : 'Start again' }}
              </button>
              <button type="button" class="lx-action" title="Remove this card and its runs" @click="forgetGroup(current)">
                <Trash2 class="w-3.5 h-3.5" /> Clear
              </button>
            </template>
          </div>
        </header>

        <!--
          A session dispatched to a SLURM partition: its queue, here, while
          it waits and while it runs — who is ahead, which nodes are busy.
        -->
        <queue-panel
          v-if="currentQueue"
          class="pt-3 border-t border-gray-100"
          :queue="currentQueue"
          :job-id="currentJobId"
        />

        <!-- The runs, newest first, each folded until wanted. -->
        <details
          v-for="(run, index) in current.runs"
          :key="run.id"
          class="lx-run"
          :open="openRuns[run.id] === true"
          @toggle="openRuns[run.id] = $event.target.open"
        >
          <summary>
            <ChevronRight class="lx-chevron w-3.5 h-3.5" />
            <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="dot(run.status)" />
            <span class="font-medium text-gray-700">{{ index === 0 ? 'Latest run' : 'Earlier run' }}</span>
            <span>· started {{ new Date(run.startedAt).toLocaleTimeString() }} · {{ statusLabel(run) }}</span>
            <span v-if="run.url" class="lx-mono truncate ml-auto">{{ run.url }}</span>
          </summary>
          <ansi-output
            v-if="openRuns[run.id]"
            :text="logText(run.id)"
            :active="run.status === 'running'"
            :label="`Output of ${run.label}`"
            placeholder="Waiting for output…"
            max-height="55vh"
          />
        </details>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronRight, ExternalLink, LayoutDashboard, Play, Square, Trash2 } from 'lucide-vue-next'
import AnsiOutput from '@dashboard/components/diagnostics/AnsiOutput.vue'
import QueuePanel from '../components/QueuePanel.vue'
import { jobIdFromLog, queueOf } from '../lib/slurm.js'
import { desktop, openExternal, wantsNewWindow } from '../bridge.js'
import { state, attempt, loadLog, openDashboard, refreshProcesses, restartProcess } from '../state.js'
import { usePageKeys } from '../composables/pageKeys.js'

const route = useRoute()
const router = useRouter()
const selected = ref(null)
const restarting = ref(false)
/** Which runs are unfolded; none to begin with. */
const openRuns = reactive({})

/**
 * One card per thing started: the runs of the same server or session —
 * same kind, same name — gathered together, newest first.
 */
const groups = computed(() => {
  const byKey = new Map()
  for (const process of state.processes) {
    const key = `${process.kind}:${process.label}`
    if (!byKey.has(key)) byKey.set(key, { key, runs: [] })
    byKey.get(key).runs.push(process)
  }
  const list = [...byKey.values()].map(group => {
    group.runs.sort((left, right) => right.startedAt - left.startedAt)
    group.latest = group.runs[0]
    return group
  })
  return list.sort((left, right) => {
    const running = Number(right.latest.status === 'running') - Number(left.latest.status === 'running')
    return running || right.latest.startedAt - left.latest.startedAt
  })
})
const current = computed(() => groups.value.find(group => group.key === selected.value) || null)

/** The queue of the selected session, when it was dispatched to one. */
const currentQueue = computed(() => queueOf(state.launches[current.value?.latest?.id]?.options))
/** Its job, read off the log once the worker reported it. */
const currentJobId = computed(() => jobIdFromLog(state.logs[current.value?.latest?.id] || []))
// The log is what names the job: loaded for a queued session as soon as it is selected.
watch(() => [current.value?.latest?.id, Boolean(currentQueue.value)], async ([id, queued]) => {
  if (id && queued && !state.logs[id]) await loadLog(id)
}, { immediate: true })

function logText(id) {
  return (state.logs[id] || []).join('\n')
}

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

function canRestart(process) {
  return process.kind !== 'setup' && Boolean(state.launches[process.id])
}

async function select(key) {
  selected.value = key
}

// The keyboard's cursor is the selection, however it was made: the first
// `j` then moves on from the selected card, not from the top.
watch(selected, key => place(groups.value.findIndex(group => group.key === key)), { immediate: true })

/** Open what a card stands for: the dashboard for a server, the browser for a notebook. */
function open(group, event = null) {
  const latest = group?.latest
  if (!latest?.url || latest.status !== 'running') return
  if (latest.kind === 'server') openDashboard(latest.url, { newWindow: wantsNewWindow(event) })
  else if (latest.kind === 'notebook') openExternal(latest.url)
}

// j and k move the selection itself; the letters do what the buttons do.
const { place } = usePageKeys({
  page: 'processes',
  count: () => groups.value.length,
  onCursor: index => { selected.value = groups.value[index]?.key || null },
  actions: {
    Enter: (index, event) => open(groups.value[index], event),
    o: (index, event) => open(groups.value[index], event),
    x: index => {
      const latest = groups.value[index]?.latest
      if (latest?.status === 'running') stop(latest)
    },
    s: index => {
      const latest = groups.value[index]?.latest
      if (latest && latest.status !== 'running' && latest.status !== 'stopping' && canRestart(latest)) restart(latest)
    },
    l: index => {
      const latest = groups.value[index]?.latest
      if (latest) openRuns[latest.id] = true
    },
    h: index => {
      const latest = groups.value[index]?.latest
      if (latest) openRuns[latest.id] = false
    },
    q: index => {
      const queue = queueOf(state.launches[groups.value[index]?.latest?.id]?.options)
      if (queue) router.push({ name: 'queues', query: { ssh: queue.ssh || '', partition: queue.partition } })
    }
  }
})

// The runs being looked at load their output when unfolded.
watch(openRuns, async opened => {
  for (const [id, open] of Object.entries(opened)) {
    if (open && !state.logs[id]) await loadLog(id)
  }
})

async function stop(process) {
  await attempt(() => desktop.stopProcess(process.id))
}

/** Run it again with the options it was started with; the new run joins the card. */
async function restart(process) {
  restarting.value = true
  const started = await attempt(() => restartProcess(process), `Starting ${process.label} again.`, 'processes')
  restarting.value = false
  if (started) openRuns[started.id] = true
}

async function forgetGroup(group) {
  for (const run of group.runs) {
    if (run.status === 'running' || run.status === 'stopping') continue
    await attempt(() => desktop.forgetProcess(run.id))
    state.processes = state.processes.filter(entry => entry.id !== run.id)
    delete state.logs[run.id]
    delete state.launches[run.id]
  }
  if (!groups.value.some(entry => entry.key === group.key)) selected.value = groups.value[0]?.key || null
}

/** Coming from a "running" pill, or the status bar, selects that card. */
function applyQuery() {
  const id = route.query.process
  if (!id) return
  const group = groups.value.find(entry => entry.runs.some(run => run.id === id))
  if (group) selected.value = group.key
}

onMounted(async () => {
  await refreshProcesses()
  applyQuery()
  if (!selected.value && groups.value.length) selected.value = groups.value[0].key
})

watch(groups, list => {
  if (!selected.value && list.length) selected.value = list[0].key
})
watch(() => route.query.process, applyQuery)
</script>
