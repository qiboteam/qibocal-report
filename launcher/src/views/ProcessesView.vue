<template>
  <div class="max-w-5xl mx-auto px-5 py-8">
    <div class="mb-5 flex items-start gap-4">
      <div class="min-w-0">
        <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Running</h1>
        <p class="mt-1 text-xs text-gray-500">
          Everything the launcher started, one card per server or session, with every run since the
          application was opened. Stopping is graceful: sessions get the chance to close their tunnels first.
        </p>
      </div>
      <!-- Where New server sits on Servers, quieter: the tint of the home page's section icons. -->
      <router-link
        :to="{ name: 'queues' }"
        class="ml-auto shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#ebe0ff] text-[#3b107e] text-xs font-semibold hover:bg-[#dfd0ff] transition"
        title="The SLURM queues of the sessions (g q)"
      >
        <ListOrdered class="w-3.5 h-3.5" /> Queues
      </router-link>
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
            <!-- An agent and the report server of its configuration lead to each other. -->
            <router-link
              v-if="linkedServer(current.latest)"
              :to="{ query: { process: linkedServer(current.latest).id } }"
              class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-medium hover:bg-emerald-100 transition"
              title="Its configuration's report server, in Running"
            >reports running</router-link>
            <router-link
              v-if="linkedAgent(current.latest)"
              :to="{ query: { process: linkedAgent(current.latest).id } }"
              class="px-2 py-0.5 rounded-full bg-purple-50 text-[#833dff] text-[11px] font-medium hover:bg-purple-100 transition"
              :title="`The runs of ${agentServed(current.latest).name}, whose reports this serves`"
            >agent {{ agentServed(current.latest).name }}</router-link>
            <!-- A server is read in the embedded dashboard, a notebook in the browser. -->
            <button
              v-if="current.latest.url && current.latest.kind === 'server' && current.latest.status === 'running'"
              type="button"
              class="lx-action"
              title="Open it in the dashboard; it is registered only with Register"
              @click="openDashboard(current.latest.url, { newWindow: wantsNewWindow($event) })"
              @auxclick.prevent="$event.button === 1 && openDashboard(current.latest.url, { newWindow: true })"
            >
              <LayoutDashboard class="w-3.5 h-3.5" /> Dashboard
            </button>
            <!-- Started for a look: it can still be kept. -->
            <button
              v-if="current.latest.kind === 'server' && current.latest.status === 'running' && unregistered(current.latest)"
              type="button"
              class="lx-action"
              title="Keep it in servers.json, as if started with Start and register"
              @click="register(current.latest)"
            >
              <Bookmark class="w-3.5 h-3.5" /> Register
            </button>
            <button
              v-if="current.latest.url && current.latest.kind === 'notebook' && current.latest.status === 'running'"
              type="button"
              class="lx-action"
              @click="openExternal(current.latest.url)"
            >
              <ExternalLink class="w-3.5 h-3.5" /> Browser
            </button>
            <!-- The reports a session writes: a server on the same channel, read in the dashboard. -->
            <button
              v-if="current.latest.kind === 'notebook' && state.launches[current.latest.id]?.options"
              type="button"
              class="lx-action"
              title="Start a report server on the same machine, serving the session's working directory; open it in the dashboard while it runs"
              @click="sessionReports(current.latest)"
            >
              <LayoutDashboard class="w-3.5 h-3.5" /> Reports
            </button>
            <!-- An agent's prompt, kept for the next runs: under a name typed here. -->
            <form v-if="promptOf(current.latest) && naming.id === current.latest.id" class="flex items-center gap-1.5" @submit.prevent="keepPrompt(current.latest)">
              <input v-model.trim="naming.name" type="text" class="lx-input !py-1 !w-36" placeholder="Name" aria-label="Name of the prompt" />
              <button type="submit" class="lx-action" :disabled="!naming.name"><Bookmark class="w-3.5 h-3.5" /> Save</button>
              <button type="button" class="lx-action" title="Cancel" @click="naming.id = null"><X class="w-3.5 h-3.5" /></button>
            </form>
            <button
              v-else-if="promptOf(current.latest)"
              type="button"
              class="lx-action"
              title="Save the prompt of this run, to choose it in the next ones"
              @click="Object.assign(naming, { id: current.latest.id, name: '' })"
            >
              <Bookmark class="w-3.5 h-3.5" /> Save prompt
            </button>
            <!-- The reports of the agent's configuration — all its runs — on a server of their own. -->
            <button
              v-if="current.latest.kind === 'agent' && agentName(current.latest)"
              type="button"
              class="lx-action"
              :title="linkedServer(current.latest)
                ? 'Open the reports of its configuration in the dashboard'
                : 'Start the report server of its configuration, serving all its runs; it goes on after the agent stops'"
              @click="agentReports(current.latest)"
            >
              <LayoutDashboard class="w-3.5 h-3.5" /> Reports
            </button>
            <button
              v-if="current.latest.kind === 'agent' && current.latest.status === 'running' && linkedServer(current.latest)"
              type="button"
              class="lx-action"
              title="Stop the agent and its report server together"
              @click="stopBoth(current.latest)"
            >
              <Square class="w-3.5 h-3.5" /> Stop both
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
          :job-name="currentJobName"
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
import { Bookmark, ChevronRight, ExternalLink, LayoutDashboard, ListOrdered, Play, Square, Trash2, X } from 'lucide-vue-next'
import AnsiOutput from '@dashboard/components/diagnostics/AnsiOutput.vue'
import QueuePanel from '../components/QueuePanel.vue'
import { jobIdFromLog, jobNameFromLog, queueOf } from '../lib/slurm.js'
import { agentOfReportsKey, agentReportsKey } from '../lib/agents.js'
import { desktop, openExternal, wantsNewWindow } from '../bridge.js'
import {
  state,
  attempt,
  loadLog,
  openDashboard,
  refreshProcesses,
  registerServer,
  restartProcess,
  agentRunOf,
  notebookReportsServer,
  startAgentReports,
  savePrompt,
  unregisteredServers,
  startNotebookReports
} from '../state.js'
import { usePageKeys } from '../composables/pageKeys.js'

const route = useRoute()
const router = useRouter()
const selected = ref(null)
const restarting = ref(false)
/** Which runs are unfolded; none to begin with. */
const openRuns = reactive({})
/** The agent run whose prompt is being named, to be saved. */
const naming = reactive({ id: null, name: '' })

/**
 * The prompt an agent run was given — or, given none, its configuration's
 * own objective — when there is one to keep.
 */
function promptOf(process) {
  if (process?.kind !== 'agent') return ''
  const options = state.launches[process.id]?.options || {}
  if (options.objective) return options.objective
  const entry = state.agents?.document?.agents?.[options.name]
  return typeof entry?.objective === 'string' ? entry.objective : ''
}

async function keepPrompt(process) {
  const name = naming.name
  const saved = await attempt(() => savePrompt(name, promptOf(process)), `Prompt ${name} saved: Run offers it.`, 'processes')
  if (saved !== undefined) naming.id = null
}

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
/** Its name, said at submission: the job is found by it before the id exists. */
const currentJobName = computed(() => jobNameFromLog(state.logs[current.value?.latest?.id] || []))
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

/** A running server that is in no configuration file: started for a look. */
function unregistered(process) {
  return unregisteredServers().some(entry => entry.id === process.id)
}

/** Keep a server that was started for a look, as Servers does. */
async function register(process) {
  await attempt(
    () => registerServer({
      name: process.label,
      url: process.url,
      description: `Started by the launcher: ${process.detail}`
    }),
    `${process.label} registered.`,
    'servers'
  )
}

/** A session's reports: its report server started, or opened in the dashboard while it runs. */
/** The configuration an agent run is of. */
function agentName(process) {
  return process?.kind === 'agent' ? state.launches[process.id]?.options?.name || null : null
}

/** The report server of an agent run's configuration, while it runs. */
function linkedServer(process) {
  const name = agentName(process)
  return name ? notebookReportsServer(agentReportsKey(name)) : null
}

/** The configuration a report server serves, when it is an agent's. */
function agentServed(process) {
  return process?.kind === 'server' ? agentOfReportsKey(state.launches[process.id]?.notebook) : null
}

/** The run of the configuration a report server serves: the one going on, or its latest. */
function linkedAgent(process) {
  const served = agentServed(process)
  return served?.host === 'local' ? agentRunOf(served.name) : null
}

/** Its configuration's reports: opened when its server runs, started otherwise. */
async function agentReports(process) {
  const running = linkedServer(process)
  const started = await attempt(
    () => startAgentReports(agentName(process)),
    running ? null : 'Starting the report server of the configuration; it appears in the dashboard once it answers.',
    'processes'
  )
  if (started?.id && !running) router.replace({ query: { process: started.id } })
}

/** The agent, and the report server of its configuration, in one go. */
async function stopBoth(process) {
  const server = linkedServer(process)
  await attempt(() => Promise.all([desktop.stopProcess(process.id), server && desktop.stopProcess(server.id)]))
}

async function sessionReports(process) {
  const options = state.launches[process.id]?.options || {}
  const started = await attempt(
    () => startNotebookReports(options, options.connection || null),
    'Starting the report server of the session; it appears in the dashboard once it answers.',
    'processes'
  )
  // A new server: its card, where its address appears.
  if (started?.id && started.id !== process.id) router.replace({ query: { process: started.id } })
}

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
    r: index => {
      const latest = groups.value[index]?.latest
      if (latest?.kind === 'server' && latest.status === 'running' && unregistered(latest)) register(latest)
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
