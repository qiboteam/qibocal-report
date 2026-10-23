<template>
  <div class="max-w-5xl mx-auto px-5 py-10">
    <div class="text-center mb-9">
      <h1 class="text-2xl sm:text-3xl font-semibold text-gray-900 tracking-tight">
        Qibocamp on this machine
      </h1>
      <p class="mt-1.5 text-xs sm:text-sm text-gray-500 max-w-xl mx-auto">
        Start report servers, open notebook sessions and browse your reports, without leaving the application.
      </p>
    </div>

    <!-- One size for every card: the grid stretches them, the descriptions are of a length. -->
    <div ref="grid" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 items-stretch">
      <button
        type="button"
        class="bm-card text-left p-5 flex items-start gap-3.5 hover:-translate-y-px transition min-h-[6.5rem]"
        :class="{ 'lx-focus': cursor === 0 }"
        @click="openDashboard(null, { newWindow: wantsNewWindow($event) })"
        @auxclick.prevent="$event.button === 1 && openDashboard(null, { newWindow: true })"
      >
        <span class="w-9 h-9 rounded-xl bg-[#833dff] text-white inline-flex items-center justify-center shrink-0">
          <LayoutDashboard class="w-4.5 h-4.5" />
        </span>
        <span>
          <span class="block text-sm font-semibold text-gray-900">Dashboard</span>
          <span class="block mt-0.5 text-xs text-gray-500">
            Browse the reports, with every server the launcher knows already connected.
          </span>
        </span>
      </button>

      <router-link
        v-for="(section, index) in others"
        :key="section.name"
        :to="section.path"
        class="bm-card p-5 flex items-start gap-3.5 hover:-translate-y-px transition min-h-[6.5rem]"
        :class="{ 'lx-focus': cursor === index + 1 }"
      >
        <span class="w-9 h-9 rounded-xl bg-[#ebe0ff] text-[#3b107e] inline-flex items-center justify-center shrink-0">
          <component :is="sectionIcons[section.icon]" class="w-4.5 h-4.5" />
        </span>
        <span>
          <span class="block text-sm font-semibold text-gray-900">
            {{ section.title }}
            <span v-if="badge(section.name)" class="ml-1.5 text-[11px] font-medium text-gray-400">
              {{ badge(section.name) }}
            </span>
          </span>
          <span class="block mt-0.5 text-xs text-gray-500">{{ section.summary }}</span>
        </span>
      </router-link>
    </div>

    <!--
      What runs right now, in a line each: the way to its card in Running,
      and the way to where it is used — the dashboard for a server, the
      browser for a notebook, Configuration for an installation. On the
      keyboard, the lines come below the last row of cards.
    -->
    <section class="mt-8">
      <div class="flex items-center gap-2 px-1 mb-2">
        <h2 class="text-sm font-semibold text-gray-900">Running now</h2>
        <span v-if="live.length" class="text-xs text-gray-400">{{ live.length }}</span>
      </div>
      <p v-if="!live.length" class="px-1 text-xs text-gray-400">Nothing is running.</p>
      <div v-else class="bm-card divide-y divide-gray-100">
        <div
          v-for="(process, index) in live"
          :key="process.id"
          class="flex items-center gap-3 px-4 py-2.5 first:rounded-t-xl last:rounded-b-xl"
          :class="{ 'lx-focus': cursor === cards + index }"
        >
          <span class="lx-dot" :class="process.status === 'running' ? 'bg-emerald-500' : 'bg-amber-500'" />
          <span class="min-w-0 flex-1">
            <span class="block text-xs font-medium text-gray-900 truncate">
              {{ process.label }}
              <span class="ml-1.5 text-[10px] uppercase tracking-wide text-gray-400 font-normal">{{ kindLabel(process) }}</span>
            </span>
            <span class="block lx-mono text-gray-500 truncate">{{ process.url || process.detail }}</span>
          </span>
          <router-link
            :to="{ name: 'processes', query: { process: process.id } }"
            class="lx-action"
            title="Its card in Running, with the output"
          >
            <Activity class="w-3.5 h-3.5" /> Running
          </router-link>
          <button
            v-if="process.kind === 'server' && process.url"
            type="button"
            class="lx-action"
            title="Read its reports in the dashboard"
            @click="openDashboard(process.url, { newWindow: wantsNewWindow($event) })"
            @auxclick.prevent="$event.button === 1 && openDashboard(process.url, { newWindow: true })"
          >
            <LayoutDashboard class="w-3.5 h-3.5" /> Dashboard
          </button>
          <button
            v-else-if="process.kind === 'notebook' && process.url"
            type="button"
            class="lx-action"
            title="Open the session in the browser"
            @click="openExternal(process.url)"
          >
            <ExternalLink class="w-3.5 h-3.5" /> Browser
          </button>
          <router-link
            v-else-if="process.kind === 'setup'"
            to="/settings"
            class="lx-action"
            title="The installation, in Configuration"
          >
            <Settings class="w-3.5 h-3.5" /> Configuration
          </router-link>
        </div>
      </div>
    </section>

    <!--
      The SLURM queues of the sessions that run: how busy each is, and my
      own jobs in it. Read from what Running last asked, or asked once on
      arrival; never polled from here, the controller being left alone.
    -->
    <section v-if="queues.length" class="mt-6">
      <div class="flex items-center gap-2 px-1 mb-2">
        <h2 class="text-sm font-semibold text-gray-900">Queues</h2>
        <span class="text-xs text-gray-400">{{ queues.length }}</span>
        <router-link to="/queues" class="ml-auto text-xs text-gray-500 hover:text-gray-900">All queues</router-link>
      </div>
      <div class="bm-card divide-y divide-gray-100">
        <div v-for="item in queues" :key="item.key" class="px-4 py-2.5">
          <div class="flex items-center gap-2 text-xs">
            <router-link
              :to="{ name: 'queues', query: { ssh: item.queue.ssh || '', partition: item.queue.partition } }"
              class="font-medium text-gray-900 hover:text-[#3b107e] lx-mono"
            >{{ item.queue.partition }}</router-link>
            <span v-if="item.queue.ssh" class="text-gray-400 truncate" :title="item.queue.ssh">on {{ item.machine }}</span>
            <span v-if="item.entry?.data?.summary?.available === false" class="text-red-700 font-medium">down</span>
            <span class="ml-auto text-[11px] text-gray-400 whitespace-nowrap">
              <template v-if="item.entry?.loading && !item.entry?.data">asking…</template>
              <template v-else-if="item.entry?.fetchedAt">{{ timeAgo(item.entry.fetchedAt, now) }}</template>
            </span>
          </div>
          <p v-if="item.entry?.error" class="mt-0.5 text-[11px] text-amber-800">{{ item.entry.error }}</p>
          <template v-else-if="item.entry?.data">
            <p class="mt-0.5 text-[11px] text-gray-500">{{ describeOccupation(item.entry.data.summary) }}</p>
            <p class="mt-0.5 text-[11px] text-gray-600 flex flex-wrap gap-x-3 gap-y-0.5">
              <span class="text-gray-400">mine:</span>
              <template v-if="item.mine.length">
                <span v-for="job in item.mine" :key="job.id" class="inline-flex items-center gap-1">
                  <span class="lx-dot" :class="jobDot(job.state)" />
                  <span class="lx-mono">{{ job.id }}</span>
                  <span class="truncate max-w-[10rem]" :title="job.name">{{ job.name }}</span>
                  <span class="text-gray-400">{{ job.state.toLowerCase() }}<template v-if="job.time && job.time !== '0:00'"> · {{ job.time }}</template></span>
                </span>
              </template>
              <span v-else class="text-gray-400">none</span>
            </p>
          </template>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Activity, ExternalLink, LayoutDashboard, Settings } from 'lucide-vue-next'
import { sections } from '../router.js'
import { sectionIcons } from '../icons.js'
import { openExternal, openInNewWindow, wantsNewWindow } from '../bridge.js'
import { state, machines, openDashboard, queueEntry, refreshQueue } from '../state.js'
import { registerPageKeys } from '../shortcuts.js'
import { pageShortcuts } from '../pagekeys.js'
import { describeOccupation, groupMachines, ownJobs, queueKey, queueOf } from '../lib/slurm.js'
import { timeAgo } from '../lib/time.js'

const router = useRouter()

/** The cards, in the order of use: what runs, then what to start. */
const ORDER = ['processes', 'servers', 'notebooks', 'agents', 'settings', 'help']
const others = ORDER.map(name => sections.find(section => section.name === name)).filter(Boolean)
/** How many cards there are: the dashboard, then the sections. */
const cards = others.length + 1

const running = computed(() => state.processes.filter(process => process.status === 'running').length)
const connections = computed(() => Object.keys(state.notebooks || {}).length)
/** Everything alive: running, or still being stopped. */
const live = computed(() => state.processes.filter(process => process.status === 'running' || process.status === 'stopping'))

function badge(name) {
  if (name === 'servers' && state.servers.length) return `${state.servers.length} registered`
  if (name === 'processes' && running.value) return `${running.value} running`
  if (name === 'notebooks' && connections.value) return `${connections.value} saved`
  return ''
}

function kindLabel(process) {
  if (process.kind === 'setup') return 'installation'
  return process.kind
}

// --- The queues of the sessions that run ---------------------------------------

/** One line per queue with a live session on it, with what it last answered and my jobs in it. */
const queues = computed(() => {
  const byKey = new Map()
  for (const process of live.value) {
    // Notebooks, and agents: each operation of one is a job of its own.
    if (process.kind !== 'notebook' && process.kind !== 'agent') continue
    const queue = queueOf(state.launches[process.id]?.options)
    if (queue && !byKey.has(queueKey(queue))) byKey.set(queueKey(queue), { key: queueKey(queue), queue })
  }
  // By machine, as Queues groups them; each named as the application's machines are.
  const order = groupMachines([...byKey.values()].map(item => item.queue), machines.value)
  return order.flatMap(machine => machine.partitions.map(({ key, queue }) => {
    const entry = queueEntry(queue)
    return { key, queue, machine: machine.label, entry, mine: ownJobs(entry?.data) }
  }))
})

function jobDot(jobState) {
  const key = String(jobState || '').toUpperCase()
  if (key.startsWith('RUNNING')) return 'bg-emerald-500'
  if (key.startsWith('PENDING')) return 'bg-amber-400'
  return 'bg-gray-300'
}

const now = ref(Date.now())
let ticker = null
// Asked once on arrival — served from the last answer when it is recent —
// and not again while here: the home page does not poll the controller.
onMounted(() => {
  ticker = setInterval(() => { now.value = Date.now() }, 15_000)
  for (const item of queues.value) refreshQueue(item.queue).catch(() => {})
})
onBeforeUnmount(() => clearInterval(ticker))

// --- The keyboard: the cards as the grid they are, the lines below them -----

const grid = ref(null)
/** The card or line under the cursor, counting cards first; -1 for none. */
const cursor = ref(-1)

/** How many cards share a row: read off the page, since the grid reflows with the window. */
function columns() {
  const children = [...(grid.value?.children || [])]
  if (!children.length) return 1
  const top = children[0].offsetTop
  return Math.max(1, children.filter(child => child.offsetTop === top).length)
}

function total() {
  return cards + live.value.length
}

/**
 * Move in a direction. Within the cards, `h` and `l` step along the row
 * and `j` and `k` by a row; from the last row, `j` reaches the first line
 * of what runs, and the lines are walked one by one.
 */
function move(key) {
  const count = total()
  if (!count) return false
  const width = columns()
  let next = cursor.value
  if (next < 0) {
    next = key === 'k' || key === 'h' ? count - 1 : 0
  } else if (next < cards) {
    const row = Math.floor(next / width)
    const column = next % width
    if (key === 'h') next = Math.max(row * width, next - 1)
    else if (key === 'l') next = Math.min(cards - 1, row * width + Math.min(width - 1, column + 1))
    else if (key === 'k') next = row === 0 ? next : next - width
    else if (key === 'j') {
      const below = next + width
      next = below < cards ? below : (live.value.length ? cards : next)
    }
  } else {
    if (key === 'j') next = Math.min(count - 1, next + 1)
    else if (key === 'k') next = next - 1 >= cards ? next - 1 : Math.max(0, cards - width)
  }
  cursor.value = next
  nextTick(() => document.querySelector('.lx-focus')?.scrollIntoView({ block: 'nearest' }))
  return true
}

/** What the cursor is on: open it, as a click would — in a new window with Shift. */
function activate(event) {
  const index = cursor.value
  if (index < 0) return false
  const newWindow = wantsNewWindow(event)
  if (index === 0) openDashboard(null, { newWindow })
  else if (index < cards) {
    if (newWindow) openInNewWindow(`#${others[index - 1].path}`)
    else router.push(others[index - 1].path)
  } else {
    const process = live.value[index - cards]
    if (!process) return false
    const route = { name: 'processes', query: { process: process.id } }
    if (newWindow) openInNewWindow(router.resolve(route).href)
    else router.push(route)
  }
  return true
}

/** Where what runs is used: the dashboard, the browser, Configuration. */
function consume(event) {
  const process = live.value[cursor.value - cards]
  if (!process) return false
  if (process.kind === 'server' && process.url) openDashboard(process.url, { newWindow: wantsNewWindow(event) })
  else if (process.kind === 'notebook' && process.url) openExternal(process.url)
  else if (process.kind === 'setup') router.push('/settings')
  else return false
  return true
}

function handle(event) {
  switch (event.key) {
    case 'h': case 'j': case 'k': case 'l': return move(event.key)
    case 'Enter': return activate(event)
    case 'o': return consume(event)
    case 'Escape':
      if (cursor.value < 0) return false
      cursor.value = -1
      return true
    default: return false
  }
}

let unregister = null
onMounted(() => {
  unregister = registerPageKeys(handle)
  state.pageShortcuts = pageShortcuts('home')
})
onBeforeUnmount(() => {
  unregister?.()
  if (state.pageShortcuts?.title === 'Home') state.pageShortcuts = null
})
watch(total, count => {
  if (cursor.value >= count) cursor.value = count - 1
})
</script>
