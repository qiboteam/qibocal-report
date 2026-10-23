<!--
  The SLURM queues the launcher knows — those of the sessions and agents it
  runs, of the saved connections and configurations — by the machine they
  are on: a tree of machines and their partitions, as Running lists its
  cards; a machine's partitions at a glance, or one partition with room for
  its whole table. Each machine is asked once for all its queues.
-->
<template>
  <div class="max-w-6xl mx-auto px-5 py-8 space-y-5">
    <div class="flex items-start gap-4">
      <div class="min-w-0">
        <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Queues</h1>
        <p class="mt-1 text-xs text-gray-500">
          What the SLURM partitions are doing, machine by machine: the jobs ahead of a session, the nodes busy or
          down. Each machine is asked every {{ pollSeconds }} seconds while one of its queues is on screen, once for
          all of them, and left alone otherwise.
        </p>
      </div>
      <button
        v-if="machines.length"
        type="button"
        class="ml-auto shrink-0 lx-action"
        :title="treeOpen ? 'Hide the machines, for room' : 'Show the machines'"
        @click="toggleTree"
      >
        <component :is="treeOpen ? PanelLeftClose : PanelLeftOpen" class="w-3.5 h-3.5" /> Machines
      </button>
    </div>

    <p v-if="!machines.length && !selected" class="bm-card p-6 text-center text-xs text-gray-500">
      No queue to look at: a notebook session or an agent dispatched to a SLURM partition — running, or saved as a
      connection or a configuration — brings its queue here.
      <span class="flex items-center justify-center gap-3 mt-2">
        <router-link to="/notebooks" class="text-[#833dff] hover:text-[#3b107e]">Notebooks</router-link>
        <router-link to="/agents" class="text-[#833dff] hover:text-[#3b107e]">Agents</router-link>
      </span>
    </p>

    <div v-else class="grid gap-4 items-start" :class="treeOpen ? 'lg:grid-cols-[13rem_minmax(0,1fr)]' : ''">
      <!-- The machines, each with its partitions: narrow, and hidden at will for the table's sake. -->
      <aside v-if="treeOpen" class="bm-card p-2 space-y-1 lg:sticky lg:top-4" aria-label="Machines and partitions">
        <div v-for="machine in machines" :key="machine.key">
          <router-link
            :to="{ name: 'queues', query: { ssh: machine.ssh || '' } }"
            class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs transition"
            :class="selected?.machine === machine.key && !selected?.partition ? 'bg-purple-50 text-[#3b107e] font-semibold' : 'text-gray-800 hover:bg-gray-50 font-medium'"
            :title="machine.ssh || 'Partitions this machine reaches itself'"
          >
            <Server class="w-3.5 h-3.5 shrink-0 text-gray-400" />
            <span class="truncate flex-1">{{ machine.label }}</span>
            <span v-if="running(machine)" class="text-[10px] text-emerald-700 shrink-0">{{ running(machine) }} ●</span>
          </router-link>
          <router-link
            v-for="item in machine.partitions"
            :key="item.key"
            :to="{ name: 'queues', query: { ssh: machine.ssh || '', partition: item.queue.partition } }"
            class="flex items-center gap-1.5 pl-7 pr-2 py-1 rounded-lg text-xs transition"
            :class="selected?.partition && queueKey(selected.queue) === item.key ? 'bg-purple-50 text-[#3b107e] font-semibold' : 'text-gray-600 hover:bg-gray-50'"
          >
            <span class="lx-mono truncate flex-1">{{ item.queue.partition }}</span>
            <span v-if="sessionsOf(item.queue).length" class="text-[10px] text-emerald-700 shrink-0">{{ sessionsOf(item.queue).length }} ●</span>
          </router-link>
        </div>
      </aside>

      <!-- One partition: its whole table, and the sessions waiting in it. -->
      <section v-if="selected?.partition" class="bm-card p-4 min-w-0">
        <queue-panel :queue="selected.queue" :job-id="jobId" :job-name="jobName" full />
        <p v-if="sessionsOf(selected.queue).length" class="mt-3 text-[11px] text-gray-400">
          Sessions on this queue:
          <router-link
            v-for="process in sessionsOf(selected.queue)"
            :key="process.id"
            :to="{ name: 'processes', query: { process: process.id } }"
            class="ml-1 text-[#833dff] hover:text-[#3b107e]"
          >{{ process.label }}</router-link>
        </p>
      </section>

      <!-- One machine: a line per partition, the known ones first, the others folded. -->
      <section v-else-if="selected" class="bm-card p-4 min-w-0 space-y-3">
        <div class="flex items-center gap-2">
          <h2 class="text-sm font-semibold text-gray-900 truncate">{{ selectedMachine?.label || selected.ssh || 'This machine' }}</h2>
          <code v-if="selected.ssh && selectedMachine?.label !== selected.ssh" class="lx-mono text-gray-400 truncate">{{ selected.ssh }}</code>
          <span class="ml-auto text-[11px] text-gray-400 shrink-0">{{ asked }}</span>
          <button type="button" class="lx-action !py-0.5" title="Ask now" :disabled="machine?.loading" @click="refreshMachine(selected.ssh, { force: true })">
            <RefreshCw class="w-3 h-3" :class="{ 'lx-spin': machine?.loading }" />
          </button>
        </div>
        <p v-if="machine?.error" class="text-xs text-red-600">{{ machine.error }}</p>
        <p v-else-if="!machine?.data" class="text-xs text-gray-400">Asking the controller…</p>
        <template v-else>
          <table class="w-full text-xs">
            <thead>
              <tr class="text-left text-[11px] text-gray-400">
                <th class="font-medium py-1 pr-3">Partition</th>
                <th class="font-medium py-1 pr-3">Nodes</th>
                <th class="font-medium py-1 pr-3">Jobs</th>
                <th class="font-medium py-1 pr-3 text-right">Yours</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="line in knownLines"
                :key="line.partition"
                class="border-t border-gray-100 cursor-pointer hover:bg-purple-50/50"
                @click="openPartition(line.partition)"
              >
                <td class="py-1.5 pr-3">
                  <span class="lx-mono text-gray-900">{{ line.partition }}</span>
                  <span v-if="line.default" class="lx-tag ml-1">default</span>
                  <span v-if="line.available === false" class="ml-1 text-[10px] uppercase tracking-wide text-red-600">down</span>
                </td>
                <td class="py-1.5 pr-3 text-gray-600">{{ describeCounts(line.nodes) }}</td>
                <td class="py-1.5 pr-3 text-gray-600">{{ describeCounts(line.jobs) }}</td>
                <td class="py-1.5 pr-3 text-right" :class="line.mine ? 'text-[#833dff] font-semibold' : 'text-gray-400'">{{ line.mine || '–' }}</td>
              </tr>
            </tbody>
          </table>
          <details v-if="otherLines.length" class="lx-more">
            <summary><ChevronRight class="lx-chevron w-3.5 h-3.5" /> Other partitions on this machine ({{ otherLines.length }})</summary>
            <table class="w-full text-xs mt-1">
              <tbody>
                <tr
                  v-for="line in otherLines"
                  :key="line.partition"
                  class="border-t border-gray-100 cursor-pointer hover:bg-purple-50/50"
                  title="Look at this partition's queue"
                  @click="openPartition(line.partition)"
                >
                  <td class="py-1.5 pr-3">
                    <span class="lx-mono text-gray-700">{{ line.partition }}</span>
                    <span v-if="line.default" class="lx-tag ml-1">default</span>
                    <span v-if="line.available === false" class="ml-1 text-[10px] uppercase tracking-wide text-red-600">down</span>
                  </td>
                  <td class="py-1.5 pr-3 text-gray-500">{{ describeCounts(line.nodes) }}</td>
                  <td class="py-1.5 pr-3 text-gray-500">{{ describeCounts(line.jobs) }}</td>
                  <td class="py-1.5 pr-3 text-right" :class="line.mine ? 'text-[#833dff] font-semibold' : 'text-gray-400'">{{ line.mine || '–' }}</td>
                </tr>
              </tbody>
            </table>
          </details>
        </template>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronRight, PanelLeftClose, PanelLeftOpen, RefreshCw, Server } from 'lucide-vue-next'
import QueuePanel from '../components/QueuePanel.vue'
import { state, knownQueues, machineEntry, machines as namedMachines, queuePollSeconds, refreshMachine, watchMachine } from '../state.js'
import { groupMachines, jobIdFromLog, jobNameFromLog, machineKey, queueKey, queueOf } from '../lib/slurm.js'
import { timeAgo } from '../lib/time.js'

const route = useRoute()
const router = useRouter()
const pollSeconds = queuePollSeconds

/** Whether the tree of machines is shown: hidden, the table has the page's width. Remembered. */
const TREE_KEY = 'qibocamp_launcher_queues_tree'
const treeOpen = ref(localStorage.getItem(TREE_KEY) !== 'closed')
function toggleTree() {
  treeOpen.value = !treeOpen.value
  localStorage.setItem(TREE_KEY, treeOpen.value ? 'open' : 'closed')
}

/** What waits in a queue: notebook sessions, and agents, whose operations are jobs of their own. */
const QUEUED = new Set(['notebook', 'agent'])

/** The sessions on a queue: notebooks and agents the launcher started with that partition, still alive. */
function sessionsOf(queue) {
  const key = queueKey(queue)
  return state.processes.filter(process =>
    QUEUED.has(process.kind) && (process.status === 'running' || process.status === 'stopping') &&
    queueKey(queueOf(state.launches[process.id]?.options)) === key)
}

/** The machines and their partitions, named as the application's machines are. */
const machines = computed(() => groupMachines(knownQueues(), namedMachines.value))

/** How many sessions and agents wait on a machine's partitions. */
function running(machine) {
  return machine.partitions.reduce((total, item) => total + sessionsOf(item.queue).length, 0)
}

/**
 * What the address names: a machine — `ssh`, empty for this one — and maybe
 * one of its partitions; with neither, the first machine.
 */
const selected = computed(() => {
  if (route.query.ssh !== undefined || route.query.partition) {
    const ssh = String(route.query.ssh || '').trim() || null
    const partition = String(route.query.partition || '').trim() || null
    return { machine: machineKey(ssh), ssh, partition, queue: partition ? { ssh, partition } : null }
  }
  const first = machines.value[0]
  return first ? { machine: first.key, ssh: first.ssh, partition: null, queue: null } : null
})
const selectedMachine = computed(() => machines.value.find(machine => machine.key === selected.value?.machine) || null)

/** The machine's answer, asked while its overview is on screen. */
const machine = computed(() => (selected.value && !selected.value.partition ? machineEntry(selected.value.ssh) : null))
const knownLines = computed(() => (machine.value?.data?.partitions || []).filter(line => line.known))
const otherLines = computed(() => (machine.value?.data?.partitions || []).filter(line => !line.known))
const asked = computed(() => {
  const at = machine.value?.fetchedAt
  return at ? `asked ${timeAgo(at)}` : ''
})

let stopWatching = null
watch(() => (selected.value && !selected.value.partition ? selected.value.machine : null), (key, previous) => {
  if (key === previous) return
  stopWatching?.()
  stopWatching = key === null ? null : watchMachine(selected.value.ssh)
}, { immediate: true })
onBeforeUnmount(() => stopWatching?.())

function openPartition(partition) {
  router.push({ name: 'queues', query: { ssh: selected.value.ssh || '', partition } })
}

/** Counts by state, the larger first: "6 allocated · 2 idle". */
function describeCounts(counts = {}) {
  return Object.entries(counts)
    .filter(([, count]) => count)
    .sort(([, a], [, b]) => b - a)
    .map(([key, count]) => `${count} ${key.toLowerCase()}`)
    .join(' · ') || '–'
}

/** The job of the first running session on the partition, to mark it: by id, or by name until then. */
const jobId = computed(() => {
  for (const process of sessionsOf(selected.value?.queue || {})) {
    const id = jobIdFromLog(state.logs[process.id] || [])
    if (id) return id
  }
  return null
})
const jobName = computed(() => {
  for (const process of sessionsOf(selected.value?.queue || {})) {
    const name = jobNameFromLog(state.logs[process.id] || [])
    if (name) return name
  }
  return null
})
</script>
