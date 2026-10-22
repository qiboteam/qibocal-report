<!--
  The machines: the SSH destinations the application names once, for every
  page to offer and to group by. Each shows what uses it — notebook
  sessions, remote execution connections, servers, agent configurations,
  those kept for it — and its queues; the destinations in use that no
  machine names yet are offered to be named.
-->
<template>
  <div class="max-w-5xl mx-auto px-5 py-8 space-y-5">
    <div class="min-w-0">
      <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Machines</h1>
      <p class="mt-1 text-xs text-gray-500">
        The machines reached over SSH, named once, in <code class="lx-mono">machines.json</code>: every page offers them where
        it asks for an SSH destination, and shows a connection by its machine's name. The connections still store the
        destination itself, as the command line, qibocal-widgets and qibocal-agent read it.
      </p>
    </div>

    <section class="space-y-2.5">
      <div class="flex items-center gap-2 px-1">
        <h2 class="text-sm font-semibold text-gray-900">Named</h2>
        <span class="text-xs text-gray-400">{{ list.length }}</span>
      </div>
      <div class="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
        <article v-for="machine in list" :key="machine.name" class="bm-card p-3.5 flex flex-col gap-2 min-w-0">
          <div class="flex items-start gap-2">
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-gray-900 truncate">{{ machine.name }}</p>
              <p class="lx-mono text-gray-500 truncate" :title="machine.ssh">{{ machine.ssh }}</p>
            </div>
            <button type="button" class="lx-action shrink-0" title="Change its destination" @click="startEdit(machine)"><Pencil class="w-3.5 h-3.5" /></button>
            <button
              type="button"
              class="lx-action shrink-0"
              :disabled="keptFor(machine) > 0"
              :title="keptFor(machine) ? 'Agent configurations are kept for it: move or remove them first' : 'Forget its name: what uses it keeps its destination'"
              @click="remove(machine)"
            ><Trash2 class="w-3.5 h-3.5" /></button>
          </div>

          <form v-if="editing.name === machine.name" class="space-y-2" @submit.prevent="saveEdit(machine)">
            <input v-model.trim="editing.ssh" type="text" class="lx-input lx-mono" aria-label="SSH destination" spellcheck="false" autocomplete="off" />
            <label v-if="usesOf(machine, uses).length" class="flex items-center gap-1.5 text-[11px] text-gray-600">
              <input v-model="editing.move" type="checkbox" class="accent-[#833dff]" />
              Move what uses it to the new destination ({{ usesOf(machine, uses).length }})
            </label>
            <div class="flex items-center gap-1.5">
              <button type="submit" class="lx-primary !py-1" :disabled="!editing.ssh || editing.busy">Save</button>
              <button type="button" class="lx-action" @click="editing.name = null">Cancel</button>
            </div>
          </form>

          <!-- What uses it, each leading to the page that holds it. -->
          <ul v-if="usesOf(machine, uses).length" class="space-y-0.5 text-[11px]">
            <li v-for="group in groupedUses(machine)" :key="group.kind" class="flex flex-wrap gap-x-1.5">
              <span class="text-gray-400">{{ group.label }}:</span>
              <router-link v-for="use in group.uses" :key="use.name" :to="group.to" class="text-[#833dff] hover:text-[#3b107e]">{{ use.name }}</router-link>
            </li>
          </ul>
          <p v-else class="text-[11px] text-gray-400">Nothing uses it yet.</p>
          <router-link
            v-if="hasQueues(machine)"
            :to="{ name: 'queues', query: { ssh: machine.ssh } }"
            class="text-[11px] text-[#833dff] hover:text-[#3b107e]"
          >Its queues</router-link>
        </article>

        <form class="bm-card p-3.5 space-y-2" @submit.prevent="add(fresh.name, fresh.ssh)">
          <input v-model.trim="fresh.name" type="text" class="lx-input lx-mono" placeholder="lab" aria-label="Name of the machine" spellcheck="false" autocomplete="off" />
          <input v-model.trim="fresh.ssh" type="text" class="lx-input lx-mono" placeholder="user@access-node" aria-label="SSH destination of the machine" spellcheck="false" autocomplete="off" />
          <button type="submit" class="lx-action" :disabled="Boolean(nameError(fresh.name)) || !fresh.name || !fresh.ssh"><Plus class="w-3.5 h-3.5" /> Add machine</button>
          <p class="lx-help !mt-0">{{ nameError(fresh.name) || 'A name, and the SSH destination as ssh takes it: an alias of the SSH configuration, or user@host.' }}</p>
        </form>
      </div>
    </section>

    <!-- Destinations in use that no machine names yet: named here, in one go. -->
    <section v-if="unnamed.length" class="space-y-2.5">
      <div class="flex items-center gap-2 px-1">
        <h2 class="text-sm font-semibold text-gray-900">In use, not named</h2>
        <span class="text-xs text-gray-400">{{ unnamed.length }}</span>
      </div>
      <div class="bm-card divide-y divide-gray-100">
        <form v-for="ssh in unnamed" :key="ssh" class="flex flex-wrap items-center gap-2 px-4 py-2.5 text-xs" @submit.prevent="add(naming[ssh], ssh)">
          <code class="lx-mono text-gray-700 truncate min-w-0 flex-1" :title="ssh">{{ ssh }}</code>
          <span class="text-[11px] text-gray-400">{{ usersOf(ssh) }}</span>
          <input v-model.trim="naming[ssh]" type="text" class="lx-input lx-mono !w-36" placeholder="Name it" :aria-label="`Name for ${ssh}`" spellcheck="false" autocomplete="off" />
          <button type="submit" class="lx-action" :disabled="!naming[ssh] || Boolean(nameError(naming[ssh]))"><Tag class="w-3.5 h-3.5" /> Name it</button>
        </form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive } from 'vue'
import { Pencil, Plus, Tag, Trash2 } from 'lucide-vue-next'
import {
  state, attempt, knownQueues, machines as list, refreshAgents, refreshNotebooks, refreshRemotes, saveMachines
} from '../state.js'
import { destinationUses, machineNameError, unnamedDestinations, usesOf, withMachine, withoutMachine } from '../lib/machines.js'

const fresh = reactive({ name: '', ssh: '' })
const editing = reactive({ name: null, ssh: '', move: true, busy: false })
const naming = reactive({})

const uses = computed(() => destinationUses({
  notebooks: state.notebooks,
  remotes: state.remotes,
  agents: state.agents?.document,
  hosts: state.agentHosts,
  launches: state.preferences?.launches,
  servers: state.servers
}))
const unnamed = computed(() => unnamedDestinations(uses.value, list.value))

/** What uses a machine, by kind, each leading to its page. */
const KINDS = [
  { kind: 'notebook', label: 'Notebooks', to: { name: 'notebooks' } },
  { kind: 'remote', label: 'Remote execution', to: { name: 'remotes' } },
  { kind: 'server', label: 'Servers', to: { name: 'servers' } },
  { kind: 'agent', label: 'Agents', to: { name: 'agents' } },
  { kind: 'kept', label: 'Agents kept for it', to: { name: 'agents' } }
]
function groupedUses(machine) {
  const own = usesOf(machine, uses.value)
  return KINDS
    .map(kind => ({ ...kind, uses: own.filter(use => use.kind === kind.kind) }))
    .filter(group => group.uses.length)
}

/** What uses an unnamed destination, in a few words. */
function usersOf(ssh) {
  const own = uses.value.filter(use => use.ssh === ssh)
  return KINDS.map(kind => [kind.label, own.filter(use => use.kind === kind.kind).length])
    .filter(([, count]) => count)
    .map(([label, count]) => `${label} ${count}`)
    .join(' · ')
}

const keptFor = machine => Object.keys(state.agentHosts?.[machine.name]?.agents || {}).length
const hasQueues = machine => knownQueues().some(queue => queue.ssh === machine.ssh)
const nameError = name => machineNameError(name, state.machines)

async function add(name, ssh) {
  const saved = await attempt(() => saveMachines(withMachine(state.machines, name, ssh)), `Machine ${name} added.`, 'machines')
  if (saved === undefined) return
  Object.assign(fresh, { name: '', ssh: '' })
  delete naming[ssh]
}

function startEdit(machine) {
  Object.assign(editing, { name: machine.name, ssh: machine.ssh, move: true, busy: false })
}

async function saveEdit(machine) {
  editing.busy = true
  const moved = editing.move ? { from: machine.ssh, to: editing.ssh } : null
  const saved = await attempt(
    () => saveMachines(withMachine(state.machines, machine.name, editing.ssh), { moved }),
    moved ? `${machine.name} moved to ${editing.ssh}, with what used it.` : `${machine.name} now reaches ${editing.ssh}.`,
    'machines'
  )
  editing.busy = false
  if (saved !== undefined) editing.name = null
}

async function remove(machine) {
  await attempt(() => saveMachines(withoutMachine(state.machines, machine.name)), `Machine ${machine.name} forgotten.`, 'machines')
}

onMounted(() => Promise.all([refreshAgents(), refreshNotebooks(), refreshRemotes()]).catch(() => {}))
</script>
