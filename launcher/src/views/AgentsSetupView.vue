<!--
  What the Agents page shares among its configurations, on a page of its own:
  how it fits together, the qibocal-agent it runs and registers, and the one
  MCP registration; the machines are the application's, on Machines.
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
          assistant or autonomous runs here, or <em>another machine</em>, for an assistant running there, which reads it from
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
          An assistant on another machine registers the same, with the path of the qibocal-agent there.
        </p>
      </div>

    </section>

    <!-- The machines configurations are kept for, or reach: the application's, on a page of their own. -->
    <p class="bm-card p-4 text-xs text-gray-500">
      The machines a configuration is kept for, or starts its calibration server on, are the application's:
      <router-link :to="{ name: 'machines' }" class="text-[#833dff] hover:text-[#3b107e]">Machines</router-link>
      names them, and shows what each one serves.
    </p>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Copy, Download, FolderOpen, RotateCcw } from 'lucide-vue-next'
import { chooseDirectory, desktop } from '../bridge.js'
import { state, attempt, fail, installAgentTools, notify, refreshAgents, refreshAgentTools } from '../state.js'
import { mcpSnippet } from '../lib/agents.js'

/** The repository qibocal-agent is installed from. */
const TOOLS_REPOSITORY = 'qiboteam/qibocal-mcp-servers'

const router = useRouter()

const toolsRef = ref('main')
const toolsRefs = ref([])
const installing = ref(false)

const tools = computed(() => state.preferences?.agentTools || '')
const toolsInfo = computed(() => state.agentTools)
const snippet = computed(() => mcpSnippet(toolsInfo.value?.executable))

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
