<!--
  What the Agents page shares among its configurations, on a page of its own:
  how it fits together, the qibocal-agent it runs and registers, the one MCP
  registration, and the SSH remotes the configurations reach.
-->
<template>
  <div class="max-w-4xl mx-auto px-5 py-8 space-y-5">
    <div class="flex items-start gap-4">
      <div class="min-w-0">
        <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Agents - Setup</h1>
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
      <router-link :to="{ name: 'agents' }" class="ml-auto shrink-0 lx-action" title="Back to the configurations">
        <ArrowLeft class="w-3.5 h-3.5" /> Agents
      </router-link>
    </div>

    <section class="bm-card p-4 space-y-4">
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

    </section>

    <!-- SSH remotes: named once, reached by several configurations; a grid, as each says little. -->
    <section class="space-y-2.5">
      <div class="flex items-center gap-2 px-1">
        <h2 class="text-sm font-semibold text-gray-900">Remotes</h2>
        <span class="text-xs text-gray-400">{{ remotes.length }}</span>
      </div>
      <div class="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
        <article v-for="remote in remotes" :key="remote.name" class="bm-card p-3.5 flex items-start gap-2">
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-gray-900 truncate">{{ remote.name }}</p>
            <p class="lx-mono text-gray-500 truncate" :title="remote.ssh">{{ remote.ssh }}</p>
            <p class="text-[11px] text-gray-400 mt-0.5">{{ remote.kept }} kept · {{ reachingCount(remote) }} reaching it</p>
          </div>
          <button type="button" class="lx-action shrink-0" :disabled="remote.kept > 0" :title="remote.kept ? 'It keeps configurations: move or remove them first' : 'Forget this remote'" @click="removeRemote(remote)"><Trash2 class="w-3.5 h-3.5" /></button>
        </article>
        <form class="bm-card p-3.5 space-y-2" @submit.prevent="addRemote">
          <input v-model.trim="newRemote.name" type="text" class="lx-input lx-mono" placeholder="lab" aria-label="Name of the remote" spellcheck="false" autocomplete="off" />
          <input v-model.trim="newRemote.ssh" type="text" class="lx-input lx-mono" placeholder="user@access-node" aria-label="SSH destination of the remote" spellcheck="false" autocomplete="off" />
          <button type="submit" class="lx-action" :disabled="Boolean(remoteError) || !newRemote.name || !newRemote.ssh"><Plus class="w-3.5 h-3.5" /> Add remote</button>
        </form>
      </div>
      <p class="lx-help px-1">{{ remoteError || 'A name, and the SSH destination as ssh takes it: an alias of the SSH configuration, or user@host.' }}</p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Copy, Download, FolderOpen, Plus, RotateCcw, Trash2 } from 'lucide-vue-next'
import { chooseDirectory, desktop } from '../bridge.js'
import { state, attempt, fail, installAgentTools, notify, refreshAgents, refreshAgentTools } from '../state.js'
import { agentConfigurations, agentRemotes, mcpSnippet, reachedRemote, withRemote, withoutRemote } from '../lib/agents.js'

/** The repository qibocal-agent is installed from. */
const TOOLS_REPOSITORY = 'qiboteam/qibocal-mcp-servers'

const router = useRouter()

const newRemote = reactive({ name: '', ssh: '' })
const toolsRef = ref('main')
const toolsRefs = ref([])
const installing = ref(false)

const configurations = computed(() => agentConfigurations(state.agents.document, state.agentHosts))
const remotes = computed(() => agentRemotes(state.agentHosts))
const tools = computed(() => state.preferences?.agentTools || '')
const toolsInfo = computed(() => state.agentTools)
const snippet = computed(() => mcpSnippet(toolsInfo.value?.executable))
const remoteError = computed(() => {
  if (!newRemote.name) return ''
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(newRemote.name)) return 'A name is a letter or digit, then letters, digits, dots, underscores or hyphens.'
  return remotes.value.some(remote => remote.name === newRemote.name) ? `${newRemote.name} is a remote already.` : ''
})

/** How many configurations start their server on a remote. */
function reachingCount(remote) {
  return configurations.value.filter(item => reachedRemote(item.entry, remotes.value) === remote.name).length
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    notify('Copied.', 'agents')
  } catch (error) {
    fail(error)
  }
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
  if (saved !== undefined) state.agentHosts = saved
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
