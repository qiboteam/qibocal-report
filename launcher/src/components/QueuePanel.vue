<!--
  What a SLURM queue is doing, for the session waiting in it or running
  from it: the partition's nodes in one line, the jobs in a table — ours
  first and marked — with a few filters. The queue is asked sparingly: once
  when the panel appears, then every so many seconds while it is on screen,
  and on request. Several panels on the same queue share one question.
-->
<template>
  <section class="space-y-2.5">
    <header class="flex flex-wrap items-center gap-x-3 gap-y-1">
      <!-- Explicit gaps: the template's whitespace between the spans is dropped. -->
      <h3 class="text-xs font-semibold text-gray-900 flex items-baseline gap-1.5">
        <span>Queue</span>
        <span class="lx-mono font-normal text-gray-500">{{ queue.partition }}</span>
        <span v-if="queue.ssh" class="font-normal text-gray-400">on <span class="lx-mono">{{ queue.ssh }}</span></span>
      </h3>
      <span v-if="standing" class="px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 text-[11px] font-medium">
        {{ standing }}
      </span>
      <span class="ml-auto text-[11px] text-gray-400 whitespace-nowrap">
        <template v-if="entry?.loading && !entry?.data">asking…</template>
        <template v-else-if="entry?.fetchedAt">updated {{ timeAgo(entry.fetchedAt, now) }}</template>
      </span>
      <button type="button" class="lx-action" title="Ask the queue now" :disabled="entry?.loading" @click="refreshQueue(queue, { force: true })">
        <RefreshCw class="w-3.5 h-3.5" :class="{ 'lx-spin': entry?.loading }" /> Refresh
      </button>
      <router-link v-if="!full" :to="{ name: 'queues', query: { ssh: queue.ssh || '', partition: queue.partition } }" class="lx-action" title="The queue on a page of its own">
        <Maximize2 class="w-3.5 h-3.5" /> Full view
      </router-link>
    </header>

    <p v-if="entry?.error" class="text-xs text-amber-800 bg-amber-50 rounded-xl px-3 py-2">{{ entry.error }}</p>

    <template v-if="entry?.data">
      <!-- The partition: its nodes by state, and whether it is up at all. -->
      <p class="text-xs text-gray-600 flex flex-wrap items-center gap-x-3 gap-y-1">
        <span v-if="entry.data.summary.available === false" class="text-red-700 font-medium">partition down</span>
        <span>{{ describeNodes(entry.data.summary) || 'no node information' }}</span>
        <span class="text-gray-400">·</span>
        <span>{{ entry.data.summary.total_jobs }} job{{ entry.data.summary.total_jobs === 1 ? '' : 's' }}<template v-if="entry.data.summary.jobs.PENDING">, {{ entry.data.summary.jobs.PENDING }} pending</template></span>
      </p>

      <!-- Filters: mine, by state, by text. -->
      <div class="flex flex-wrap items-center gap-1.5">
        <button
          v-if="entry.data.user"
          type="button"
          class="lx-chip"
          :class="{ 'is-on': filters.mine }"
          :title="`Only the jobs of ${entry.data.user}`"
          @click="filters.mine = !filters.mine"
        >mine</button>
        <button
          v-for="state in JOB_STATES"
          :key="state"
          type="button"
          class="lx-chip"
          :class="{ 'is-on': filters.states.includes(state) }"
          @click="toggleState(state)"
        >{{ state.toLowerCase() }}<span v-if="entry.data.summary.jobs[state]" class="ml-1 text-gray-400">{{ entry.data.summary.jobs[state] }}</span></button>
        <input
          v-model.trim="filters.search"
          type="search"
          class="lx-input !py-1 !px-2 w-40 ml-auto"
          placeholder="Filter…"
          aria-label="Filter the jobs"
          spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off"
        />
      </div>

      <!--
        In a card, the table keeps to a share of the window and scrolls
        within itself, its header staying put; on its own page it has the room.
      -->
      <div class="lx-list is-scrolling bg-white" :class="full ? '' : 'max-h-[45vh]'">
        <!-- Columns as the dashboard's table has them: dragged at their edge, reset by a double click, remembered. -->
        <table class="text-xs table-fixed" :style="{ width: `${totalTableWidth}px`, minWidth: '100%' }">
          <thead class="sticky top-0 bg-white z-10">
            <tr class="text-[11px] text-gray-400 text-left">
              <th
                v-for="(column, index) in columns"
                :key="column.key"
                class="relative font-medium px-3 py-1.5 select-none"
                :style="{ width: `${column.width}px`, minWidth: `${column.minWidth}px` }"
              >
                <div class="truncate pr-2">{{ column.label }}</div>
                <div
                  class="absolute right-0 top-0 bottom-0 w-3 cursor-col-resize select-none flex justify-center items-center group/resizer z-10"
                  :title="`Drag to resize; double-click to reset`"
                  @mousedown.stop.prevent="startResize(index, $event)"
                  @dblclick.stop="resetColumnWidth(index)"
                  @click.stop
                >
                  <div class="w-[2px] h-full transition-colors" :class="resizingIndex === index ? 'bg-[#833dff]' : 'bg-transparent group-hover/resizer:bg-[#833dff]/70'"></div>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="job in shown"
              :key="job.id"
              class="border-t border-gray-100"
              :class="isOwnJob(job, own) ? 'bg-[#f7f5ff] text-gray-900' : 'text-gray-700'"
            >
              <td class="px-3 py-1.5 lx-mono truncate" :title="job.id">
                {{ job.id }}
                <span v-if="isOwnJob(job, own)" class="ml-1 text-[10px] uppercase tracking-wide text-[#833dff] font-semibold">this session</span>
              </td>
              <td class="px-3 py-1.5 truncate" :title="job.name">{{ job.name }}</td>
              <td class="px-3 py-1.5 truncate" :title="job.user">{{ job.user }}</td>
              <td class="px-3 py-1.5 truncate">
                <span class="lx-dot mr-1.5 align-middle" :class="dot(job.state)" />{{ job.state.toLowerCase() }}
              </td>
              <td class="px-3 py-1.5 lx-mono truncate" :title="job.time_limit ? `limit ${job.time_limit}` : ''">{{ job.time }}</td>
              <td class="px-3 py-1.5 lx-mono truncate" :title="job.nodes || job.reason">
                <template v-if="job.nodes">{{ job.nodes }}</template>
                <span v-else class="text-gray-400">{{ job.reason ? `waiting: ${job.reason}` : '—' }}</span>
              </td>
            </tr>
            <tr v-if="!shown.length">
              <td colspan="6" class="px-3 py-3 text-center text-gray-400">{{ entry.data.jobs.length ? 'Nothing matches the filters.' : 'The queue is empty.' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="text-[11px] text-gray-400">
        Refresh rate: {{ pollSeconds }} s
      </p>
    </template>
    <p v-else-if="!entry?.error" class="text-xs text-gray-400">Asking the queue…</p>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Maximize2, RefreshCw } from 'lucide-vue-next'
import { useTableColumns } from '@dashboard/composables/useTableColumns.js'
import { state, queueEntry, queuePollSeconds, refreshQueue, watchQueue } from '../state.js'
import { JOB_STATES, describeNodes, filterJobs, isOwnJob, positionOf, queueKey } from '../lib/slurm.js'
import { timeAgo } from '../lib/time.js'

const props = defineProps({
  /** `{ ssh, partition }`: the queue to look at. */
  queue: { type: Object, required: true },
  /** The id of this session's job, when known: marked, and first. */
  jobId: { type: String, default: null },
  /** The name the worker gave the job: marks it until the id is known. */
  jobName: { type: String, default: null },
  /** On the page of its own: no link to it. */
  full: { type: Boolean, default: false }
})

const filters = reactive({ mine: false, states: [], search: '' })
const entry = computed(() => queueEntry(props.queue))
const own = computed(() => ({ jobId: props.jobId, jobName: props.jobName }))

/** The columns, dragged at their edge and remembered, as the dashboard's table does. */
const { columns, totalTableWidth, resizingIndex, startResize, resetColumnWidth } = useTableColumns([
  { key: 'id', label: 'Job', width: 110, minWidth: 60, resizable: true },
  { key: 'name', label: 'Name', width: 200, minWidth: 80, resizable: true },
  { key: 'user', label: 'User', width: 100, minWidth: 60, resizable: true },
  { key: 'state', label: 'State', width: 110, minWidth: 70, resizable: true },
  { key: 'time', label: 'Time', width: 90, minWidth: 60, resizable: true },
  { key: 'nodes', label: 'Nodes', width: 220, minWidth: 80, resizable: true }
], 'qibocamp_launcher_queue_columns_v1')
const pollSeconds = queuePollSeconds
const shown = computed(() => filterJobs(entry.value?.data?.jobs || [], {
  mine: filters.mine,
  user: entry.value?.data?.user,
  states: filters.states,
  search: filters.search,
  jobId: props.jobId,
  jobName: props.jobName
}))
/** Where our job stands, while it waits. */
const standing = computed(() => {
  const position = positionOf(entry.value?.data?.jobs || [], props.jobId, props.jobName)
  return position ? `${position}${ordinal(position)} in line` : ''
})

function ordinal(n) {
  const rest = n % 100
  if (rest >= 11 && rest <= 13) return 'th'
  return { 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] || 'th'
}

function toggleState(stateName) {
  filters.states = filters.states.includes(stateName)
    ? filters.states.filter(entry => entry !== stateName)
    : [...filters.states, stateName]
}

function dot(jobState) {
  const key = String(jobState || '').toUpperCase()
  if (key.startsWith('RUNNING')) return 'bg-emerald-500'
  if (key.startsWith('PENDING')) return 'bg-amber-400'
  if (key.startsWith('COMPLETING')) return 'bg-sky-400'
  return 'bg-gray-300'
}

/** Re-read once a minute, so "updated 2 minutes ago" keeps being true. */
const now = ref(Date.now())
let ticker = null
let unwatch = () => {}

onMounted(() => {
  ticker = setInterval(() => { now.value = Date.now() }, 15_000)
  unwatch = watchQueue(props.queue)
})
onBeforeUnmount(() => {
  clearInterval(ticker)
  unwatch()
})
watch(() => queueKey(props.queue), () => {
  unwatch()
  unwatch = watchQueue(props.queue)
})
// Nothing else reads `state` here, but the entry is reactive through it.
void state
</script>
