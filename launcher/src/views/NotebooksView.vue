<template>
  <div class="max-w-4xl mx-auto px-5 py-8 space-y-5">
    <div class="flex items-start gap-4">
      <div class="min-w-0">
        <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Notebooks</h1>
        <p class="mt-1 text-xs text-gray-500">
          A JupyterLab or Marimo session runs here, over SSH, or through SLURM. Registered sessions are the very
          connections <code class="lx-mono">qibocal notebook</code> uses.
        </p>
      </div>
      <!-- The form for a new session opens from here; the page starts on the sessions it has. -->
      <button
        type="button"
        class="ml-auto shrink-0 lx-primary"
        :class="{ 'is-open': creating }"
        :aria-expanded="creating"
        :title="creating ? 'Close the form' : 'New session'"
        @click="creating = !creating"
      >
        <component :is="creating ? X : Plus" class="w-3.5 h-3.5" /> {{ creating ? 'Close' : 'New session' }}
      </button>
    </div>

    <!-- One form for every new session; nothing is required, and empty it is a local one. -->
    <section v-if="creating" class="bm-card p-5">
      <h2 class="text-sm font-semibold text-gray-900 mb-4">New session</h2>
      <notebook-fields
        :values="form"
        :errors="created.errors"
        :warnings="created.warnings"
        named
        :name-error="newNameError"
      />

      <div class="flex flex-wrap items-center gap-2.5 mt-5">
        <!-- Registering is the rule; opening for a look, the exception. -->
        <button
          type="button"
          class="lx-primary"
          :disabled="!created.valid || !form.name || Boolean(newNameError) || starting"
          :title="form.name ? 'Open it, and keep it in notebooks.json for next time' : 'Give it a name to keep it'"
          @click="openNew(true)"
        >
          <Bookmark class="w-3.5 h-3.5" /> {{ starting ? 'Opening…' : 'Open and register' }}
        </button>
        <button
          type="button"
          class="lx-action"
          :disabled="!created.valid || starting"
          title="Open it for a look, without touching notebooks.json"
          @click="openNew(false)"
        >
          <Play class="w-3.5 h-3.5" /> Open
        </button>
        <span class="lx-mono text-gray-400 truncate">{{ preview }}</span>
      </div>
    </section>

    <!-- Registered sessions -->
    <section class="space-y-2.5">
      <div class="flex items-center gap-2 px-1">
        <h2 class="text-sm font-semibold text-gray-900">Registered sessions</h2>
        <span class="text-xs text-gray-400">{{ names.length }}</span>
        <button
          type="button"
          class="ml-auto text-xs text-gray-500 hover:text-gray-900 inline-flex items-center gap-1"
          @click="refreshNotebooks"
        >
          <RefreshCw class="w-3 h-3" />
          Refresh
        </button>
      </div>

      <p v-if="!names.length" class="bm-card p-5 text-xs text-gray-500">
        No session registered yet. Opening one with <em>Open and register</em> adds it here.
      </p>

      <article
        v-for="(name, index) in names"
        :key="name"
        class="bm-card p-4"
        :class="{ 'lx-focus': focused(index) }"
      >
        <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
          <div class="min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">{{ name }}</p>
            <p class="lx-mono text-gray-500 truncate">{{ describeConnection(state.notebooks[name]) }}</p>
          </div>
          <!-- The pill leads to the card of this session in Running. -->
          <router-link
            v-if="runningSession(name)"
            :to="{ name: 'processes', query: { process: runningSession(name).id } }"
            class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-medium hover:bg-emerald-100 transition"
            title="See it in Running"
          >running</router-link>

          <div class="ml-auto flex flex-wrap items-center gap-1.5">
            <!-- Running and answering: open it. Otherwise: start it. -->
            <button
              v-if="runningSession(name)?.url"
              type="button"
              class="lx-primary !py-1"
              title="Open the session in the browser"
              @click="openExternal(runningSession(name).url)"
            >
              <ExternalLink class="w-3.5 h-3.5" /> Open
            </button>
            <button
              v-else
              type="button"
              class="lx-primary !py-1"
              :disabled="starting || Boolean(runningSession(name))"
              :title="runningSession(name) ? 'Starting: its address appears in Running' : 'Start a session with these options'"
              @click="start(name)"
            >
              <Play class="w-3.5 h-3.5" /> Start
            </button>
            <!-- The reports its calibrations write: a server on the same channel, read in the dashboard. -->
            <button
              type="button"
              class="lx-action"
              :disabled="startingReports === name"
              :title="notebookReportsServer(name)
                ? 'Open its reports in the dashboard'
                : 'Start a report server on the same machine, serving the session\'s working directory, to read in the dashboard the reports its calibrations write'"
              @click="reports(name)"
            >
              <LayoutDashboard class="w-3.5 h-3.5" /> {{ startingReports === name ? 'Starting…' : 'Reports' }}
            </button>
            <button
              type="button"
              class="lx-action"
              :disabled="rebuilding === name || Boolean(runningSession(name))"
              :title="runningSession(name)
                ? 'Stop its session first: the environment is in use'
                : 'Delete the kernel environment entirely, and create it again from qibocal and the requirements alone'"
              @click="rebuild(name)"
            >
              <RefreshCw class="w-3.5 h-3.5" :class="{ 'lx-spin': rebuilding === name }" /> {{ rebuilding === name ? 'Regenerating…' : 'Regenerate env' }}
            </button>
            <button type="button" class="lx-action" title="Edit its options" @click="toggleEdit(name)">
              <Pencil class="w-3.5 h-3.5" /> Edit
            </button>
            <button
              type="button"
              class="lx-action"
              title="Open the form for a new session with this one's options, to change a few"
              @click="duplicate(name)"
            >
              <Files class="w-3.5 h-3.5" /> Duplicate
            </button>
            <button type="button" class="lx-action" title="Forget this session" @click="remove(name)">
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <!-- Its options, in the very form of a new session, with its name. -->
        <form v-if="editing.name === name" class="mt-3.5 pt-3.5 border-t border-gray-100" @submit.prevent="saveEdit(name)">
          <notebook-fields
            :values="editing.form"
            :errors="edited.errors"
            :warnings="edited.warnings"
            named
            name-required
            :name-error="editNameError"
          />
          <div class="flex flex-wrap items-center gap-2 mt-4">
            <button type="submit" class="lx-primary" :disabled="editing.busy || !edited.valid || Boolean(editNameError)">Save</button>
            <button type="button" class="lx-action" @click="editing.name = null">Cancel</button>
            <span class="lx-mono text-gray-400 truncate">{{ commandFor(editing.form.name, edited.options) }}</span>
          </div>
        </form>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bookmark, ExternalLink, Files, LayoutDashboard, Pencil, Play, Plus, RefreshCw, Trash2, X } from 'lucide-vue-next'
import NotebookFields from '../components/NotebookFields.vue'
import { confirmAction, desktop, openExternal } from '../bridge.js'
import {
  state,
  attempt,
  fail,
  notify,
  notebookReportsServer,
  rebuildNotebook,
  startNotebookReports,
  refreshNotebooks,
  sessionsOf,
  startNotebook
} from '../state.js'
import { usePageKeys } from '../composables/pageKeys.js'
import { defaultNotebookOptions, describeConnection, normalizeNotebookOptions, toEditorValues } from '../lib/notebooks.js'

const router = useRouter()

const creating = ref(false)
const form = reactive({ ...defaultNotebookOptions(), name: '' })
/** The session being edited, with the form opened on it. */
const editing = reactive({ name: null, form: { ...defaultNotebookOptions(), name: '' }, busy: false })
const starting = ref(false)
/** The session whose environment is being rebuilt, by name. */
const rebuilding = ref(null)
/** The session whose report server is being started, by name. */
const startingReports = ref(null)

const names = computed(() => Object.keys(state.notebooks || {}))
const created = computed(() => normalizeNotebookOptions(form))
const edited = computed(() => normalizeNotebookOptions(editing.form))

const newNameError = computed(() =>
  form.name && names.value.includes(form.name) ? `A session named ${form.name} is registered already.` : ''
)
const editNameError = computed(() => {
  if (!editing.form.name) return 'A registered session needs a name.'
  if (editing.form.name !== editing.name && names.value.includes(editing.form.name)) {
    return `A session named ${editing.form.name} is registered already.`
  }
  return ''
})

/** The command a form stands for, as the command line takes it. */
function commandFor(name, options) {
  const parts = ['qibocal', 'notebook', 'connect']
  if (name) parts.push(name)
  for (const [key, value] of Object.entries(options)) {
    if (key === 'marimo') parts.push(value ? '--marimo' : '--jupyter')
    else if (key === 'requirements') parts.push('--requirements', '…')
    else parts.push(`--${key}`, String(value))
  }
  return parts.join(' ')
}
const preview = computed(() => commandFor(null, created.value.options))

/** The session of a registered name running now, if any. */
function runningSession(name) {
  return sessionsOf(name)[0] || null
}

const { focused } = usePageKeys({
  page: 'notebooks',
  count: () => names.value.length,
  actions: {
    Enter: index => activate(names.value[index]),
    s: index => activate(names.value[index]),
    e: index => toggleEdit(names.value[index]),
    d: index => duplicate(names.value[index])
  }
})

/** Open a running session, start a stopped one. */
function activate(name) {
  const running = runningSession(name)
  if (running?.url) openExternal(running.url)
  else if (!running) start(name)
}

async function launch(options, message) {
  starting.value = true
  try {
    await startNotebook(options)
    notify(message, 'processes')
    router.push({ name: 'processes' })
  } catch (error) {
    fail(error)
  } finally {
    starting.value = false
  }
}

/** The options of a registered session, beside its name: Running finds its queue in them. */
function registered(name) {
  return { connection: name, ...normalizeNotebookOptions(toEditorValues(state.notebooks[name])).options }
}

function start(name) {
  return launch(registered(name), `Opening ${name}; its address appears in Running.`)
}

async function openNew(register) {
  const { options } = created.value
  if (register) {
    const saved = await attempt(() => desktop.saveNotebook(form.name, options), `Session ${form.name} registered.`, 'notebooks')
    if (saved === undefined) return
    state.notebooks = saved
    const name = form.name
    creating.value = false
    Object.assign(form, defaultNotebookOptions(), { name: '' })
    return launch(registered(name), `Opening ${name}; its address appears in Running.`)
  }
  return launch({ ...options }, 'Opening the notebook session; its address appears in Running.')
}

function toggleEdit(name) {
  if (editing.name === name) {
    editing.name = null
    return
  }
  Object.assign(editing.form, toEditorValues(state.notebooks[name]), { name })
  Object.assign(editing, { name, busy: false })
}

async function saveEdit(name) {
  editing.busy = true
  const renamed = editing.form.name
  const saved = await attempt(async () => {
    let current = await desktop.saveNotebook(renamed, edited.value.options)
    if (renamed !== name) current = await desktop.removeNotebook(name)
    return current
  }, `Session ${renamed} saved.`, 'notebooks')
  editing.busy = false
  if (saved === undefined) return
  state.notebooks = saved
  editing.name = null
}

function duplicate(name) {
  Object.assign(form, toEditorValues(state.notebooks[name]), { name: `${name} copy` })
  creating.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function rebuild(name) {
  const venv = state.notebooks[name]?.venv || 'qibocal'
  const confirmed = await confirmAction(
    `The kernel environment "${venv}" of ${name} is deleted entirely, with everything installed in it, ` +
      'and created again from qibocal and the session\'s requirements alone. This cannot be undone.',
    { title: 'Regenerate the environment', okLabel: 'Regenerate env' }
  )
  if (!confirmed) return
  rebuilding.value = name
  const started = await attempt(
    () => rebuildNotebook(registered(name)),
    `Regenerating the environment of ${name}; its output is in Running.`,
    'processes'
  )
  rebuilding.value = null
  if (started) router.push({ name: 'processes' })
}

/** Its report server: started on the same channel, or opened in the dashboard while it runs. */
async function reports(name) {
  const running = notebookReportsServer(name)
  startingReports.value = name
  const started = await attempt(
    () => startNotebookReports(registered(name), name),
    running ? null : `Starting the report server of ${name}; it appears in the dashboard once it answers.`,
    'processes'
  )
  startingReports.value = null
  if (started && !running) router.push({ name: 'processes' })
}

async function remove(name) {
  const left = await attempt(() => desktop.removeNotebook(name), `Session ${name} removed.`, 'notebooks')
  if (left === undefined) return
  state.notebooks = left
  if (editing.name === name) editing.name = null
}

onMounted(() => refreshNotebooks())
</script>
