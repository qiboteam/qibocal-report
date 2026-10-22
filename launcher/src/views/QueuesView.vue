<!--
  The SLURM queues the launcher knows — those of the sessions it runs, and
  of the saved connections — one at a time, on a page of their own: the
  same panel as in Running, with room for the whole table.
-->
<template>
  <div class="max-w-5xl mx-auto px-5 py-8 space-y-5">
    <div class="flex items-start gap-4">
      <div class="min-w-0">
        <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Queues</h1>
        <p class="mt-1 text-xs text-gray-500">
          What a SLURM partition is doing: the jobs ahead of a session, the nodes busy or down. The controller is
          asked every {{ pollSeconds }} seconds while a queue is on screen, and left alone otherwise.
        </p>
      </div>
    </div>

    <p v-if="!known.length && !selected" class="bm-card p-6 text-center text-xs text-gray-500">
      No queue to look at: a notebook session or an agent dispatched to a SLURM partition — running, or saved as a
      connection or a configuration — brings its queue here.
      <span class="flex items-center justify-center gap-3 mt-2">
        <router-link to="/notebooks" class="text-[#833dff] hover:text-[#3b107e]">Notebooks</router-link>
        <router-link to="/agents" class="text-[#833dff] hover:text-[#3b107e]">Agents</router-link>
      </span>
    </p>

    <template v-else>
      <!-- Which queue: the known ones as chips, the current one marked. -->
      <div v-if="known.length > 1 || !selected" class="flex flex-wrap items-center gap-1.5">
        <router-link
          v-for="item in known"
          :key="item.key"
          :to="{ name: 'queues', query: { ssh: item.queue.ssh || '', partition: item.queue.partition } }"
          class="lx-chip"
          :class="{ 'is-on': selected && queueKey(selected) === item.key }"
        >
          <span class="lx-mono">{{ item.queue.partition }}</span>
          <span v-if="item.queue.ssh" class="text-gray-400 ml-1">{{ item.queue.ssh }}</span>
          <span v-if="item.sessions" class="ml-1 text-[10px] uppercase tracking-wide text-emerald-700">{{ item.sessions }} running</span>
        </router-link>
      </div>

      <section v-if="selected" class="bm-card p-4">
        <queue-panel :queue="selected" :job-id="jobId" :job-name="jobName" full />
        <p v-if="sessionsOf(selected).length" class="mt-3 text-[11px] text-gray-400">
          Sessions on this queue:
          <router-link
            v-for="process in sessionsOf(selected)"
            :key="process.id"
            :to="{ name: 'processes', query: { process: process.id } }"
            class="ml-1 text-[#833dff] hover:text-[#3b107e]"
          >{{ process.label }}</router-link>
        </p>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import QueuePanel from '../components/QueuePanel.vue'
import { state, queuePollSeconds } from '../state.js'
import { jobIdFromLog, jobNameFromLog, queueKey, queueOf } from '../lib/slurm.js'
import { agentRunOptions } from '../lib/agents.js'

const route = useRoute()
const pollSeconds = queuePollSeconds

/** What waits in a queue: notebook sessions, and agents, whose operations are jobs of their own. */
const QUEUED = new Set(['notebook', 'agent'])

/** The sessions on a queue: notebooks and agents the launcher started with that partition, still alive. */
function sessionsOf(queue) {
  const key = queueKey(queue)
  return state.processes.filter(process =>
    QUEUED.has(process.kind) && (process.status === 'running' || process.status === 'stopping') &&
    queueKey(queueOf(state.launches[process.id]?.options)) === key)
}

/** Every queue the launcher knows, the ones with sessions first. */
const known = computed(() => {
  const byKey = new Map()
  for (const process of state.processes) {
    if (!QUEUED.has(process.kind)) continue
    const queue = queueOf(state.launches[process.id]?.options)
    if (queue) byKey.set(queueKey(queue), { key: queueKey(queue), queue })
  }
  for (const options of Object.values(state.notebooks || {})) {
    const queue = queueOf(options)
    if (queue && !byKey.has(queueKey(queue))) byKey.set(queueKey(queue), { key: queueKey(queue), queue })
  }
  // The partitions of this machine's agent configurations, as their runs would wait in them.
  for (const [name, entry] of Object.entries(state.agents?.document?.agents || {})) {
    const queue = queueOf(agentRunOptions({ name }, entry))
    if (queue && !byKey.has(queueKey(queue))) byKey.set(queueKey(queue), { key: queueKey(queue), queue })
  }
  return [...byKey.values()]
    .map(item => ({ ...item, sessions: sessionsOf(item.queue).length }))
    .sort((left, right) => right.sessions - left.sessions)
})

/** The queue the address names, or the first known one. */
const selected = computed(() => {
  const partition = String(route.query.partition || '').trim()
  if (partition) return { ssh: String(route.query.ssh || '').trim() || null, partition }
  return known.value[0]?.queue || null
})

/** The job of the first running session on this queue, to mark it: by id, or by name until then. */
const jobId = computed(() => {
  for (const process of sessionsOf(selected.value || {})) {
    const id = jobIdFromLog(state.logs[process.id] || [])
    if (id) return id
  }
  return null
})
const jobName = computed(() => {
  for (const process of sessionsOf(selected.value || {})) {
    const name = jobNameFromLog(state.logs[process.id] || [])
    if (name) return name
  }
  return null
})
</script>
