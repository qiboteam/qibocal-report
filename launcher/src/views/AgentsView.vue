<template>
  <div class="max-w-4xl mx-auto px-5 py-8 space-y-5">
    <div class="flex items-start gap-4">
      <div class="min-w-0">
        <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Agents</h1>
        <p class="mt-1 text-xs text-gray-500">
          The configurations of the <a href="https://github.com/qiboteam/qibocal-mcp-servers" class="text-[#833dff] hover:text-[#3b107e]" @click.prevent="openExternal('https://github.com/qiboteam/qibocal-mcp-servers')">Qibocal MCP servers</a>:
          for an assistant on this machine, in <code class="lx-mono">{{ state.agents.path || 'agents.json' }}</code>, or for one on a
          remote, kept here and pushed there. A configuration also dispatches autonomous agents.
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

    <!-- What is not one configuration's: how it fits together, the tools, their registration, the remotes. -->
    <section class="bm-card p-5 space-y-4">
      <div>
        <h2 class="text-sm font-semibold text-gray-900">Setup</h2>
        <p class="mt-1 text-xs text-gray-500 leading-relaxed">
          A configuration says where the calibration server starts — here, or over SSH on its <em>SSH destination</em>,
          usually a cluster's access node — and, with a <em>SLURM partition</em>, that each operation runs as a job
          on the nodes reaching the instruments. It is <em>kept for</em> where its user is: <em>this machine</em>, for an
          assistant or autonomous runs here, or a <em>remote</em>, for an assistant running there, which reads it from
          its own agents.json. An assistant registers <code class="lx-mono">qibocal-agent mcp</code> once, and selects a
          configuration when it is asked to calibrate.
          <router-link :to="{ name: 'help-page', params: { page: 'agents' }, hash: '#how-it-fits-together' }" class="text-[#833dff] hover:text-[#3b107e]">How it fits together, with diagrams</router-link>, in Help.
        </p>
      </div>

      <!-- The qibocal-agent everything here runs, and registers. -->
      <div class="space-y-2">
        <div class="flex flex-wrap items-center gap-2 text-xs">
          <span class="font-semibold text-gray-700 shrink-0">qibocal-agent</span>
          <span v-if="toolsInfo?.version" class="lx-tag">{{ toolsInfo.version }}</span>
          <span v-if="toolsInfo?.managed" class="text-[10px] uppercase tracking-wide font-semibold text-[#833dff]">installed here</span>
          <code class="lx-mono text-gray-600 truncate flex-1 min-w-0" :title="toolsInfo?.executable || toolsInfo?.error || ''">
            {{ toolsInfo?.executable || toolsInfo?.error || 'Looking for it…' }}
          </code>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <input v-model.trim="toolsRef" type="text" list="agent-tools-refs" class="lx-input lx-mono !w-40" placeholder="main" spellcheck="false" autocomplete="off" title="Branch, tag or commit of qibocal-mcp-servers" />
          <datalist id="agent-tools-refs"><option v-for="ref in toolsRefs" :key="ref" :value="ref" /></datalist>
          <button type="button" class="lx-primary !py-1" :disabled="installing" :title="`Install this version in ${toolsInfo?.directory || '~/.cache/qibocal/agents/tools'}, replacing what is there; its output is in Running`" @click="installTools">
            <Download class="w-3.5 h-3.5" /> {{ toolsInfo?.installed ? 'Update' : 'Install' }}
          </button>
          <button type="button" class="lx-action" title="Use qibocal-agent from another environment" @click="chooseTools"><FolderOpen class="w-3.5 h-3.5" /> Choose environment…</button>
          <button v-if="tools" type="button" class="lx-action" title="Forget the chosen environment: the installed one, else the PATH" @click="saveTools('')"><RotateCcw class="w-3.5 h-3.5" /> Detect</button>
        </div>
        <p class="lx-help !mt-0">{{ toolsInfo?.installed ? `Installed: ${toolsInfo.installed}` : 'Installed in its own environment, with Python 3.12 or 3.13, from GitHub.' }}</p>
      </div>

      <!-- One registration for every configuration. -->
      <div class="space-y-2">
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold text-gray-700">MCP registration</span>
          <button type="button" class="lx-action ml-auto" :disabled="!toolsInfo?.executable" title="Copy the registration, for an assistant on this machine" @click="copy(snippet)"><Copy class="w-3.5 h-3.5" /> Copy</button>
        </div>
        <pre class="lx-mono text-[11px] bg-[#f7f5ff] text-[#3b107e] rounded-xl p-3 overflow-x-auto">{{ snippet }}</pre>
        <p class="lx-help !mt-0">
          For Copilot, in <code class="lx-mono">~/.copilot/mcp-config.json</code>; other assistants take the same command and arguments.
          It starts nothing by itself: the assistant lists the configurations and selects one when calibrating.
          An assistant on a remote registers the same, with the path of the qibocal-agent there.
        </p>
      </div>

      <!-- SSH remotes: named once, reached by several configurations. -->
      <div class="space-y-2">
        <span class="text-xs font-semibold text-gray-700">Remotes</span>
        <div v-for="remote in remotes" :key="remote.name" class="flex items-center gap-2 text-xs">
          <span class="font-medium text-gray-900">{{ remote.name }}</span>
          <code class="lx-mono text-gray-500 truncate min-w-0">{{ remote.ssh }}</code>
          <span class="text-gray-400">{{ remote.kept }} kept · {{ reachingCount(remote) }} reaching it</span>
          <button type="button" class="lx-action ml-auto" :disabled="remote.kept > 0" :title="remote.kept ? 'It keeps configurations: move or remove them first' : 'Forget this remote'" @click="removeRemote(remote)"><Trash2 class="w-3.5 h-3.5" /></button>
        </div>
        <form class="flex flex-wrap items-center gap-2" @submit.prevent="addRemote">
          <input v-model.trim="newRemote.name" type="text" class="lx-input lx-mono !w-36" placeholder="lab" aria-label="Name of the remote" spellcheck="false" autocomplete="off" />
          <input v-model.trim="newRemote.ssh" type="text" class="lx-input lx-mono flex-1 min-w-[12rem]" placeholder="user@access-node" aria-label="SSH destination of the remote" spellcheck="false" autocomplete="off" />
          <button type="submit" class="lx-action" :disabled="Boolean(remoteError) || !newRemote.name || !newRemote.ssh"><Plus class="w-3.5 h-3.5" /> Add remote</button>
        </form>
        <p class="lx-help !mt-0">{{ remoteError || 'A name, and the SSH destination as ssh takes it: an alias of the SSH configuration, or user@host.' }}</p>
      </div>
    </section>

    <section v-if="creating" class="bm-card p-5">
      <h2 class="text-sm font-semibold text-gray-900 mb-4">New configuration</h2>
      <agent-form :form="form" :remotes="remotes" :names="takenNames(form.host === 'local' ? 'local' : form.hostName.trim())" />
      <div class="flex flex-wrap items-center gap-2.5 mt-5">
        <button type="button" class="lx-primary" :disabled="!formValid(form) || saving" @click="create">
          <Bookmark class="w-3.5 h-3.5" /> {{ form.host === 'local' ? 'Save' : 'Save and push' }}
        </button>
        <span class="lx-help !mt-0">{{ form.host === 'local' ? 'Written to agents.json, which qibocal-agent reads.' : `Kept here, and written to agents.json on ${form.hostName || 'the remote'}.` }}</span>
      </div>
    </section>

    <section class="space-y-2.5">
      <div class="flex flex-wrap items-center gap-2 px-1">
        <h2 class="text-sm font-semibold text-gray-900">Configurations</h2>
        <span class="text-xs text-gray-400">{{ shown.length }}</span>
        <button
          type="button"
          class="ml-auto text-xs text-gray-500 hover:text-gray-900 inline-flex items-center gap-1"
          @click="refreshAgents"
        >
          <RefreshCw class="w-3 h-3" />
          Refresh
        </button>
      </div>

      <!-- Two filters, together: where a configuration is kept, and the remote it reaches. -->
      <div v-if="configurations.length" class="space-y-1.5 px-1">
        <div class="flex flex-wrap items-center gap-1.5">
          <span class="text-[11px] text-gray-400 w-16 shrink-0">Kept for</span>
          <button v-for="filter in keptFilters" :key="filter.value" type="button" class="lx-chip" :class="{ 'is-on': filters.kept === filter.value }" @click="filters.kept = filter.value">{{ filter.label }}</button>
        </div>
        <div class="flex flex-wrap items-center gap-1.5">
          <span class="text-[11px] text-gray-400 w-16 shrink-0">Reaches</span>
          <button v-for="filter in reachFilters" :key="filter.value" type="button" class="lx-chip" :class="{ 'is-on': filters.reaches === filter.value }" @click="filters.reaches = filter.value">{{ filter.label }}</button>
        </div>
      </div>

      <p v-if="!shown.length" class="bm-card p-5 text-xs text-gray-500">
        No configuration {{ configurations.length ? 'among these' : 'yet' }}. <em>New configuration</em> adds one, for this machine or a remote.
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
              <span class="ml-1.5 text-[10px] uppercase tracking-wide font-semibold" :class="item.host === 'local' ? 'text-gray-400' : 'text-[#833dff]'" :title="item.host === 'local' ? 'Kept for this machine' : `Kept for the remote ${item.host}, pushed to ${item.destination}`">{{ item.host === 'local' ? 'this machine' : `for ${item.host}` }}</span>
              <span class="ml-1 text-[10px] uppercase tracking-wide font-semibold text-gray-400" :title="reachedRemote(item.entry, remotes) ? 'Its calibration server starts there, over SSH' : 'Its calibration server starts where it runs'">{{ reachedRemote(item.entry, remotes) ? `via ${reachedRemote(item.entry, remotes)}` : 'direct' }}</span>
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
            <button v-else type="button" class="lx-primary !py-1" :disabled="pushing === item.key" :title="`Write it to agents.json on ${item.host} (${item.destination}): the configuration only, not environments`" @click="push(item)">
              <Upload class="w-3.5 h-3.5" /> {{ pushing === item.key ? 'Pushing…' : 'Push' }}
            </button>
            <button type="button" class="lx-action" :disabled="startingReports === item.key" title="Start a report server on the execution host, serving its output, and open it in the dashboard" @click="reports(item)">
              <LayoutDashboard class="w-3.5 h-3.5" /> Reports
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

        <form v-if="editing.key === item.key" class="mt-3.5 pt-3.5 border-t border-gray-100" @submit.prevent="saveEdit(item)">
          <agent-form :form="editing.form" :remotes="remotes" :names="takenNames(editing.form.host === 'local' ? 'local' : editing.form.hostName.trim(), item)" />
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
        <button type="button" class="ml-auto lx-action !py-0.5" :class="{ 'is-open': addingPrompt }" :title="addingPrompt ? 'Close' : 'Save a prompt, without running it'" @click="addingPrompt = !addingPrompt">
          <component :is="addingPrompt ? X : Plus" class="w-3.5 h-3.5" />
        </button>
      </div>
      <form v-if="addingPrompt" class="bm-card p-4 space-y-2" @submit.prevent="addPrompt">
        <input v-model.trim="newPrompt.name" type="text" class="lx-input" placeholder="Name" aria-label="Name of the prompt" />
        <textarea v-model="newPrompt.text" rows="5" class="lx-input" placeholder="Calibrate qubit 0's drive frequency using spectroscopy. Sweep no wider than 20 MHz… Stop on errors." aria-label="The prompt" />
        <div class="flex items-center gap-2">
          <button type="submit" class="lx-primary" :disabled="!newPrompt.name || !newPrompt.text.trim()"><Bookmark class="w-3.5 h-3.5" /> Save</button>
          <span class="lx-help !mt-0">{{ prompts.some(prompt => prompt.name === newPrompt.name) ? `Replaces the prompt ${newPrompt.name}.` : 'Offered by Run; a run\'s prompt can also be saved from Running.' }}</span>
        </div>
      </form>
      <p v-if="!prompts.length && !addingPrompt" class="bm-card p-5 text-xs text-gray-500">No prompt saved yet: <strong>+</strong> saves one, and so does Running, from an agent's run.</p>
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Bookmark, Copy, Download, Files, FolderOpen, LayoutDashboard, Pencil, Play, Plus, RefreshCw, RotateCcw, Trash2, Upload, X } from 'lucide-vue-next'
import AgentForm from '../components/AgentForm.vue'
import { chooseDirectory, desktop, openExternal } from '../bridge.js'
import {
  state, attempt, fail, installAgentTools, notebookReportsServer, notify, refreshAgents, refreshAgentTools,
  savePrompt, savedPrompts, startAgent, startNotebookReports
} from '../state.js'
import { usePageKeys } from '../composables/pageKeys.js'
import {
  agentConfigurations,
  agentEditorValues,
  agentEntry,
  agentNameError,
  agentRemotes,
  agentReports,
  agentShown,
  describeAgent,
  mcpSnippet,
  reachedRemote,
  withHostAgent,
  withLocalAgent,
  withRemote,
  withoutRemote
} from '../lib/agents.js'

/** The repository qibocal-agent is installed from. */
const TOOLS_REPOSITORY = 'qiboteam/qibocal-mcp-servers'

const router = useRouter()

/** A blank form: where it is kept, its name, and its settings. */
const blank = () => ({ host: 'local', hostName: '', name: '', ...agentEditorValues() })

const creating = ref(false)
const saving = ref(false)
const form = reactive(blank())
const editing = reactive({ key: null, form: blank(), busy: false })
const filters = reactive({ kept: 'all', reaches: 'all' })
const pushing = ref(null)
const startingReports = ref(null)
const run = reactive({ item: null, objective: '', busy: false })
const addingPrompt = ref(false)
const newPrompt = reactive({ name: '', text: '' })
const newRemote = reactive({ name: '', ssh: '' })
const toolsRef = ref('main')
const toolsRefs = ref([])
const installing = ref(false)

const configurations = computed(() => agentConfigurations(state.agents.document, state.agentHosts))
const remotes = computed(() => agentRemotes(state.agentHosts))
const keptFilters = computed(() => [
  { value: 'all', label: 'All' },
  { value: 'local', label: 'This machine' },
  ...remotes.value.map(remote => ({ value: remote.name, label: remote.name }))
])
const reachFilters = computed(() => {
  // The registered remotes, and any destination typed without one.
  const reached = configurations.value.map(item => reachedRemote(item.entry, remotes.value)).filter(Boolean)
  const names = [...new Set([...remotes.value.map(remote => remote.name), ...reached])]
  return [{ value: 'all', label: 'All' }, { value: 'direct', label: 'Directly' }, ...names.map(name => ({ value: name, label: name }))]
})
const shown = computed(() => configurations.value.filter(item => agentShown(item, filters, remotes.value)))
const tools = computed(() => state.preferences?.agentTools || '')
const toolsInfo = computed(() => state.agentTools)
const snippet = computed(() => mcpSnippet(toolsInfo.value?.executable))
const prompts = computed(savedPrompts)
const remoteError = computed(() => {
  if (!newRemote.name) return ''
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(newRemote.name)) return 'A name is a letter or digit, then letters, digits, dots, underscores or hyphens.'
  return remotes.value.some(remote => remote.name === newRemote.name) ? `${newRemote.name} is a remote already.` : ''
})

/** How many configurations start their server on a remote. */
function reachingCount(remote) {
  return configurations.value.filter(item => reachedRemote(item.entry, remotes.value) === remote.name).length
}

/** Names already used where a form keeps its configuration, but its own. */
function takenNames(host, own = null) {
  return configurations.value
    .filter(item => item !== own && item.host === host)
    .map(item => item.name)
    .filter(Boolean)
}

function formValid(values, own = null) {
  if (values.host !== 'local' && !remotes.value.some(remote => remote.name === values.hostName)) return false
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

/** Where a remote's configurations are pushed: its SSH destination. */
function destinationOf(host) {
  return remotes.value.find(remote => remote.name === host)?.ssh || host
}

async function drop(item) {
  if (item.host === 'local') {
    state.agents = await desktop.writeAgents(withLocalAgent(state.agents.document, item.name, null))
  } else {
    state.agentHosts = await desktop.saveAgentHosts(withHostAgent(state.agentHosts, item.host, item.name, null))
    await desktop.pushAgents(destinationOf(item.host), {}, [item.name]).catch(error => fail(`Not removed from ${item.host}: ${error?.message || error}`, 'agents'))
  }
}

async function pushOne(host, name, entry) {
  try {
    await desktop.pushAgents(destinationOf(host), { [name]: entry }, [])
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
  const ssh = item.host === 'local' ? item.entry.ssh || null : item.destination
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
  Object.assign(run, { item, objective: '', busy: false })
}

async function dispatch() {
  run.busy = true
  const objective = run.objective.trim()
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

async function addPrompt() {
  const saved = await attempt(() => savePrompt(newPrompt.name, newPrompt.text.trim()), `Prompt ${newPrompt.name} saved.`, 'agents')
  if (saved === undefined) return
  Object.assign(newPrompt, { name: '', text: '' })
  addingPrompt.value = false
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
  await refreshAgentTools().catch(() => {})
}

/** Install the version asked, as a process in Running; the status follows once it is done. */
async function installTools() {
  installing.value = true
  const started = await attempt(() => installAgentTools(toolsRef.value || 'main'), 'Installing qibocal-agent; its output is in Running.', 'processes')
  installing.value = false
  if (started) router.push({ name: 'processes', query: { process: started.id } })
}

async function addRemote() {
  const saved = await attempt(() => desktop.saveAgentHosts(withRemote(state.agentHosts, newRemote.name, newRemote.ssh)), `Remote ${newRemote.name} added.`, 'agents')
  if (saved === undefined) return
  state.agentHosts = saved
  Object.assign(newRemote, { name: '', ssh: '' })
}

async function removeRemote(remote) {
  const saved = await attempt(() => desktop.saveAgentHosts(withoutRemote(state.agentHosts, remote.name)), `Remote ${remote.name} removed.`, 'agents')
  if (saved === undefined) return
  state.agentHosts = saved
  for (const key of ['kept', 'reaches']) if (filters[key] === remote.name) filters[key] = 'all'
}

/** The branches and tags qibocal-agent can be installed from, offered with the version. */
async function loadToolsRefs() {
  const names = async kind => {
    const response = await fetch(`https://api.github.com/repos/${TOOLS_REPOSITORY}/${kind}?per_page=100`)
    return response.ok ? (await response.json()).map(ref => ref.name) : []
  }
  const [branches, tags] = await Promise.all([names('branches'), names('tags')])
  toolsRefs.value = [...new Set(['main', ...branches, ...tags])]
}

// The status follows an install, once its run ends.
watch(
  () => state.processes.filter(process => state.launches[process.id]?.kind === 'tools').map(process => process.status).join(),
  () => refreshAgentTools().catch(() => {})
)

onMounted(() => {
  refreshAgents()
  refreshAgentTools().catch(() => {})
  loadToolsRefs().catch(() => {})
})
</script>
