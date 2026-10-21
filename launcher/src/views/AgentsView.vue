<template>
  <div class="max-w-4xl mx-auto px-5 py-8 space-y-5">
    <div class="flex items-start gap-4">
      <div class="min-w-0">
        <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Agents</h1>
        <p class="mt-1 text-xs text-gray-500">
          The configurations of the <a href="https://github.com/qiboteam/qibocal-mcp-servers" class="text-[#833dff] hover:text-[#3b107e]" @click.prevent="openExternal('https://github.com/qiboteam/qibocal-mcp-servers')">Qibocal MCP servers</a>:
          for an assistant on this machine, in <code class="lx-mono">{{ state.agents.path || 'agents.json' }}</code>, or for one on an
          access node, kept here and pushed there. A configuration also dispatches autonomous agents.
        </p>
      </div>
      <button
        type="button"
        class="ml-auto shrink-0 lx-primary"
        :class="{ 'is-open': creating }"
        :aria-expanded="creating"
        :title="creating ? 'Close the form' : 'New configuration'"
        @click="creating = !creating"
      >
        <component :is="creating ? X : Plus" class="w-3.5 h-3.5" /> {{ creating ? 'Close' : 'New configuration' }}
      </button>
    </div>

    <!-- Where qibocal-agent is, to run agents and register the MCP. -->
    <div class="bm-card p-3.5 flex flex-wrap items-center gap-2 text-xs">
      <span class="text-gray-500 shrink-0">qibocal-agent</span>
      <code class="lx-mono text-gray-700 truncate flex-1 min-w-0">{{ tools || 'found on the PATH, or in ~/.cache/qibocal/envs/qibocal-agent' }}</code>
      <button type="button" class="lx-action" @click="chooseTools"><FolderOpen class="w-3.5 h-3.5" /> Choose environment…</button>
      <button v-if="tools" type="button" class="lx-action" @click="saveTools('')"><RotateCcw class="w-3.5 h-3.5" /> Detect</button>
    </div>

    <section v-if="creating" class="bm-card p-5">
      <h2 class="text-sm font-semibold text-gray-900 mb-4">New configuration</h2>
      <agent-form :form="form" :names="takenNames(form.host === 'local' ? 'local' : form.hostName.trim())" />
      <div class="flex flex-wrap items-center gap-2.5 mt-5">
        <button type="button" class="lx-primary" :disabled="!formValid(form) || saving" @click="create">
          <Bookmark class="w-3.5 h-3.5" /> {{ form.host === 'local' ? 'Save' : 'Save and push' }}
        </button>
        <span class="lx-help !mt-0">{{ form.host === 'local' ? 'Written to agents.json, which qibocal-agent reads.' : `Kept here, and written to agents.json on ${form.hostName || 'that machine'}.` }}</span>
      </div>
    </section>

    <section class="space-y-2.5">
      <div class="flex flex-wrap items-center gap-2 px-1">
        <h2 class="text-sm font-semibold text-gray-900">Configurations</h2>
        <span class="text-xs text-gray-400">{{ shown.length }}</span>
        <!-- Where they are kept: this machine, or the host they are pushed to. -->
        <div class="flex flex-wrap gap-1.5 ml-2">
          <button
            v-for="filter in filters"
            :key="filter.value"
            type="button"
            class="lx-chip"
            :class="{ 'is-on': where === filter.value }"
            @click="where = filter.value"
          >{{ filter.label }}</button>
        </div>
        <button
          type="button"
          class="ml-auto text-xs text-gray-500 hover:text-gray-900 inline-flex items-center gap-1"
          @click="refreshAgents"
        >
          <RefreshCw class="w-3 h-3" />
          Refresh
        </button>
      </div>

      <p v-if="!shown.length" class="bm-card p-5 text-xs text-gray-500">
        No configuration {{ where === 'all' ? 'yet' : 'here' }}. <em>New configuration</em> adds one, for this machine or an access node.
      </p>

      <article
        v-for="(item, index) in shown"
        :key="item.key"
        class="bm-card p-4"
        :class="{ 'lx-focus': focused(index) }"
      >
        <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
          <div class="min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">
              {{ item.name }}
              <span class="ml-1.5 text-[10px] uppercase tracking-wide font-semibold" :class="item.host === 'local' ? 'text-gray-400' : 'text-[#833dff]'">{{ item.host === 'local' ? 'this machine' : item.host }}</span>
            </p>
            <p class="lx-mono text-gray-500 truncate">{{ describeAgent(item.entry) }}</p>
          </div>
          <router-link
            v-if="runningOf(item)"
            :to="{ name: 'processes', query: { process: runningOf(item).id } }"
            class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-medium hover:bg-emerald-100 transition"
          >running</router-link>

          <div class="ml-auto flex flex-wrap items-center gap-1.5">
            <button v-if="item.host === 'local'" type="button" class="lx-primary !py-1" title="Dispatch an autonomous agent with this configuration" @click="openRun(item)">
              <Play class="w-3.5 h-3.5" /> Run
            </button>
            <button v-else type="button" class="lx-primary !py-1" :disabled="pushing === item.key" :title="`Write it to agents.json on ${item.host}: the configuration only, not environments`" @click="push(item)">
              <Upload class="w-3.5 h-3.5" /> {{ pushing === item.key ? 'Pushing…' : 'Push' }}
            </button>
            <button type="button" class="lx-action" :disabled="startingReports === item.key" title="Start a report server on the execution host, serving its output, and open it in the dashboard" @click="reports(item)">
              <LayoutDashboard class="w-3.5 h-3.5" /> Reports
            </button>
            <button v-if="item.host === 'local'" type="button" class="lx-action" title="The registration of qibocal-agent mcp for an assistant, to copy" @click="toggleSnippet(item)">
              <Braces class="w-3.5 h-3.5" /> MCP
            </button>
            <button type="button" class="lx-action" title="Edit it" @click="toggleEdit(item)">
              <Pencil class="w-3.5 h-3.5" /> Edit
            </button>
            <button type="button" class="lx-action" title="The form for a new configuration, with these settings" @click="duplicate(item)">
              <Files class="w-3.5 h-3.5" /> Duplicate
            </button>
            <button type="button" class="lx-action" title="Remove it" @click="remove(item)">
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div v-if="snippetFor === item.key" class="mt-3.5 pt-3.5 border-t border-gray-100">
          <p class="lx-help !mt-0 mb-2">For Copilot, in <code class="lx-mono">~/.copilot/mcp-config.json</code>; other assistants take the same command and arguments.</p>
          <pre class="lx-mono text-[11px] bg-[#f7f5ff] text-[#3b107e] rounded-xl p-3 overflow-x-auto">{{ mcpSnippet(item.name, tools) }}</pre>
          <button type="button" class="lx-action mt-2" @click="copy(mcpSnippet(item.name, tools))"><Copy class="w-3.5 h-3.5" /> Copy</button>
        </div>

        <form v-if="editing.key === item.key" class="mt-3.5 pt-3.5 border-t border-gray-100" @submit.prevent="saveEdit(item)">
          <agent-form :form="editing.form" :names="takenNames(editing.form.host === 'local' ? 'local' : editing.form.hostName.trim(), item)" />
          <div class="flex flex-wrap items-center gap-2 mt-4">
            <button type="submit" class="lx-primary" :disabled="editing.busy || !formValid(editing.form, item)">{{ editing.form.host === 'local' ? 'Save' : 'Save and push' }}</button>
            <button type="button" class="lx-action" @click="editing.key = null">Cancel</button>
          </div>
        </form>
      </article>
    </section>

    <!-- The prompts kept for autonomous runs: what to ask, apart from where. -->
    <section class="space-y-2.5">
      <div class="flex items-center gap-2 px-1">
        <h2 class="text-sm font-semibold text-gray-900">Saved prompts</h2>
        <span class="text-xs text-gray-400">{{ prompts.length }}</span>
      </div>
      <p v-if="!prompts.length" class="bm-card p-5 text-xs text-gray-500">No prompt saved yet: a run's prompt can be saved from its dialog.</p>
      <article v-for="(prompt, index) in prompts" :key="prompt.name" class="bm-card p-4 flex items-start gap-3">
        <div class="min-w-0 flex-1">
          <p class="text-sm font-medium text-gray-900">{{ prompt.name }}</p>
          <p class="text-xs text-gray-500 whitespace-pre-wrap line-clamp-3">{{ prompt.text }}</p>
        </div>
        <button type="button" class="lx-action shrink-0" title="Forget this prompt" @click="forgetPrompt(index)"><Trash2 class="w-3.5 h-3.5" /></button>
      </article>
    </section>

    <!-- An autonomous run: the configuration, and the prompt. -->
    <div v-if="run.item" class="lx-veil" @pointerdown.self="run.item = null">
      <form class="lx-dialog lx-dialog-sheet" @submit.prevent="dispatch">
        <h2 class="text-sm font-semibold text-gray-900 shrink-0">Run an agent: {{ run.item.name }}</h2>
        <div class="lx-dialog-scroll mt-3 space-y-3">
          <p class="text-xs text-gray-500">
            <code class="lx-mono">qibocal-agent</code> plans, runs one protocol at a time, inspects the plots and accepts or rejects
            each update. State the target, approved hardware limits, a budget and when to stop. It is
            <strong>not a hardware safety layer</strong>.
          </p>
          <div v-if="prompts.length" class="flex flex-wrap gap-1.5">
            <button v-for="prompt in prompts" :key="prompt.name" type="button" class="lx-chip" @click="run.objective = prompt.text">{{ prompt.name }}</button>
          </div>
          <textarea
            v-model="run.objective"
            rows="7"
            class="lx-input"
            :placeholder="run.item.entry.objective ? `Empty: the saved objective — ${run.item.entry.objective}` : 'Calibrate qubit 0\'s drive frequency using spectroscopy. Sweep no wider than 20 MHz… Stop on errors or insufficient evidence.'"
          />
          <div class="flex items-center gap-2">
            <input v-model.trim="run.saveAs" type="text" class="lx-input" placeholder="Save it as… (optional)" />
          </div>
          <p class="lx-help !mt-0">The model's credentials come from your shell profile; the launcher keeps none.</p>
        </div>
        <div class="mt-3 pt-3 border-t border-gray-100 flex items-center justify-end gap-2 shrink-0">
          <button type="button" class="lx-action" @click="run.item = null">Cancel</button>
          <button type="submit" class="lx-primary" :disabled="run.busy || (!run.objective.trim() && !run.item.entry.objective) || !run.item.entry.model">
            <Play class="w-3.5 h-3.5" /> {{ run.item.entry.model ? (run.busy ? 'Starting…' : 'Run') : 'Set a model first' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bookmark, Braces, Copy, Files, FolderOpen, LayoutDashboard, Pencil, Play, Plus, RefreshCw, RotateCcw, Trash2, Upload, X } from 'lucide-vue-next'
import AgentForm from '../components/AgentForm.vue'
import { chooseDirectory, desktop, openExternal } from '../bridge.js'
import { state, attempt, fail, notebookReportsServer, notify, refreshAgents, startAgent, startNotebookReports } from '../state.js'
import { usePageKeys } from '../composables/pageKeys.js'
import {
  agentConfigurations,
  agentEditorValues,
  agentEntry,
  agentNameError,
  agentReports,
  describeAgent,
  mcpSnippet,
  withHostAgent,
  withLocalAgent
} from '../lib/agents.js'

const router = useRouter()

/** A blank form: where it is kept, its name, and its settings. */
const blank = () => ({ host: 'local', hostName: '', name: '', ...agentEditorValues() })

const creating = ref(false)
const saving = ref(false)
const form = reactive(blank())
const editing = reactive({ key: null, form: blank(), busy: false })
const where = ref('all')
const pushing = ref(null)
const startingReports = ref(null)
const snippetFor = ref(null)
const run = reactive({ item: null, objective: '', saveAs: '', busy: false })

const configurations = computed(() => agentConfigurations(state.agents.document, state.agentHosts))
const filters = computed(() => [
  { value: 'all', label: 'All' },
  { value: 'local', label: 'This machine' },
  ...Object.keys(state.agentHosts || {}).map(host => ({ value: host, label: host }))
])
const shown = computed(() => configurations.value.filter(item => where.value === 'all' || item.host === where.value))
const tools = computed(() => state.preferences?.agentTools || '')
const prompts = computed(() => (Array.isArray(state.preferences?.agentPrompts) ? state.preferences.agentPrompts : []))

/** Names already used where a form keeps its configuration, but its own. */
function takenNames(host, own = null) {
  return configurations.value
    .filter(item => item !== own && item.host === host)
    .map(item => item.name)
    .filter(Boolean)
}

function formValid(values, own = null) {
  if (values.host !== 'local' && !values.hostName.trim()) return false
  if (agentNameError(values.name)) return false
  const host = values.host === 'local' ? 'local' : values.hostName.trim()
  const clash = configurations.value.some(item => item !== own && item.host === host && item.name === values.name)
  return !clash && agentEntry(values).valid
}

const { focused } = usePageKeys({
  page: 'agents',
  count: () => shown.value.length,
  actions: {
    Enter: index => { const item = shown.value[index]; if (item) item.host === 'local' ? openRun(item) : push(item) },
    e: index => toggleEdit(shown.value[index]),
    d: index => duplicate(shown.value[index])
  }
})

/** Write a configuration where it is kept — and push it, when that is another machine. */
async function store(values, previous = null) {
  const host = values.host === 'local' ? 'local' : values.hostName.trim()
  const name = values.name
  const { entry } = agentEntry(values, { previous: previous?.entry || {} })
  // Moved or renamed: the old one goes first.
  if (previous && (previous.host !== host || previous.name !== name)) await drop(previous)
  if (host === 'local') {
    const written = await desktop.writeAgents(withLocalAgent(state.agents.document, name, entry))
    state.agents = written
  } else {
    state.agentHosts = await desktop.saveAgentHosts(withHostAgent(state.agentHosts, host, name, entry))
    await pushOne(host, name, entry)
  }
}

async function drop(item) {
  if (item.host === 'local') {
    state.agents = await desktop.writeAgents(withLocalAgent(state.agents.document, item.name, null))
  } else {
    state.agentHosts = await desktop.saveAgentHosts(withHostAgent(state.agentHosts, item.host, item.name, null))
    await desktop.pushAgents(item.host, {}, [item.name]).catch(error => fail(`Not removed from ${item.host}: ${error?.message || error}`, 'agents'))
  }
}

async function pushOne(host, name, entry) {
  try {
    await desktop.pushAgents(host, { [name]: entry }, [])
    notify(`${name} written to agents.json on ${host}.`, 'agents')
  } catch (error) {
    fail(`${name} is kept here, but not pushed to ${host}: ${error?.message || error}. Push it again when the host is reachable.`, 'agents')
  }
}

async function create() {
  saving.value = true
  const done = await attempt(() => store(form), null, 'agents')
  saving.value = false
  if (done === undefined) return
  creating.value = false
  Object.assign(form, blank())
}

function toggleEdit(item) {
  if (!item) return
  if (editing.key === item.key) {
    editing.key = null
    return
  }
  Object.assign(editing.form, blank(), agentEditorValues(item.entry), {
    host: item.host === 'local' ? 'local' : 'remote',
    hostName: item.host === 'local' ? '' : item.host,
    name: item.name
  })
  Object.assign(editing, { key: item.key, busy: false })
}

async function saveEdit(item) {
  editing.busy = true
  const done = await attempt(() => store(editing.form, item), null, 'agents')
  editing.busy = false
  if (done !== undefined) editing.key = null
}

function duplicate(item) {
  if (!item) return
  Object.assign(form, blank(), agentEditorValues(item.entry), {
    host: item.host === 'local' ? 'local' : 'remote',
    hostName: item.host === 'local' ? '' : item.host,
    name: `${item.name}-copy`
  })
  creating.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function remove(item) {
  await attempt(() => drop(item), `${item.name} removed.`, 'agents')
  if (editing.key === item.key) editing.key = null
}

async function push(item) {
  pushing.value = item.key
  await pushOne(item.host, item.name, item.entry)
  pushing.value = null
}

/** Its reports: a server on the execution host, serving its output. */
async function reports(item) {
  startingReports.value = item.key
  const ssh = item.host === 'local' ? item.entry.ssh || null : item.host
  const options = { ssh, reports: agentReports(item.entry, item.name) }
  const key = `agent:${item.key}`
  const running = notebookReportsServer(key)
  const started = await attempt(
    () => startNotebookReports(options, `${item.name} agent`, { key }),
    running ? null : 'Starting the report server of the agent; it appears in the dashboard once it answers.',
    'processes'
  )
  startingReports.value = null
  if (started && !running) router.push({ name: 'processes' })
}

function toggleSnippet(item) {
  snippetFor.value = snippetFor.value === item.key ? null : item.key
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    notify('Copied.', 'agents')
  } catch (error) {
    fail(error)
  }
}

/** The run of this configuration, while it lasts. */
function runningOf(item) {
  return state.processes.find(process =>
    process.kind === 'agent' && (process.status === 'running' || process.status === 'stopping') &&
    state.launches[process.id]?.options?.name === item.name && item.host === 'local') || null
}

function openRun(item) {
  Object.assign(run, { item, objective: '', saveAs: '', busy: false })
}

async function dispatch() {
  run.busy = true
  const objective = run.objective.trim()
  if (run.saveAs && objective) {
    const kept = prompts.value.filter(prompt => prompt.name !== run.saveAs)
    await savePreferences({ agentPrompts: [...kept, { name: run.saveAs, text: objective }] })
  }
  const started = await attempt(
    () => startAgent({ name: run.item.name, objective: objective || null }),
    `Agent ${run.item.name} dispatched; its output is in Running.`,
    'processes'
  )
  run.busy = false
  if (started) {
    run.item = null
    router.push({ name: 'processes', query: { process: started.id } })
  }
}

async function forgetPrompt(index) {
  await savePreferences({ agentPrompts: prompts.value.filter((_, position) => position !== index) })
}

/** Save the preferences with `changes`; `replace` writes them as given, to drop a key. */
async function savePreferences(changes, { replace = false } = {}) {
  const next = replace ? changes : { ...state.preferences, ...changes }
  const saved = await attempt(() => desktop.savePreferences(next), null, 'agents')
  if (saved !== undefined) state.preferences = saved
}

async function chooseTools() {
  const picked = await attempt(() => chooseDirectory('Choose the environment holding qibocal-agent'))
  if (picked) await saveTools(picked)
}

async function saveTools(path) {
  const { agentTools: _old, ...rest } = state.preferences || {}
  await savePreferences(path ? { ...rest, agentTools: path } : rest, { replace: true })
}

onMounted(() => refreshAgents())
</script>
