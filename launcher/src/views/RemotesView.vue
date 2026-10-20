<template>
  <div class="max-w-4xl mx-auto px-5 py-8 space-y-5">
    <div class="flex items-start gap-4">
      <div class="min-w-0">
        <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Remote execution</h1>
        <p class="mt-1 text-xs text-gray-500">
          Where qibocal-widgets' <code class="lx-mono">Remote</code> plugin runs the acquisitions of a notebook — over SSH,
          through SLURM — while fits and reports stay with the notebook. A notebook picks one with
          <code class="lx-mono">Remote(connection="name")</code>, or through <code class="lx-mono">QIBOCAL_WIDGETS_CONNECTION</code>.
          Kept in <code class="lx-mono">remotes.json</code>, which the plugin reads.
        </p>
      </div>
      <button
        type="button"
        class="ml-auto shrink-0 lx-primary"
        :class="{ 'is-open': creating }"
        :aria-expanded="creating"
        :title="creating ? 'Close the form' : 'New connection'"
        @click="creating = !creating"
      >
        <component :is="creating ? X : Plus" class="w-3.5 h-3.5" /> {{ creating ? 'Close' : 'New connection' }}
      </button>
    </div>

    <section v-if="creating" class="bm-card p-5">
      <h2 class="text-sm font-semibold text-gray-900 mb-4">New connection</h2>
      <notebook-fields
        :values="form"
        :fields="REMOTE_FIELDS"
        :errors="created.errors"
        :warnings="created.warnings"
        named
        name-required
        name-help="What notebooks call it: Remote(connection=…), in remotes.json."
        :name-error="newNameError"
      />
      <div class="flex flex-wrap items-center gap-2.5 mt-5">
        <button
          type="button"
          class="lx-primary"
          :disabled="!created.valid || !form.name || Boolean(newNameError) || saving"
          @click="register"
        >
          <Bookmark class="w-3.5 h-3.5" /> Register
        </button>
        <span class="lx-help !mt-0">Nothing runs: notebooks use it from their next acquisition.</span>
      </div>
    </section>

    <section class="space-y-2.5">
      <div class="flex items-center gap-2 px-1">
        <h2 class="text-sm font-semibold text-gray-900">Registered connections</h2>
        <span class="text-xs text-gray-400">{{ names.length }}</span>
        <button
          type="button"
          class="ml-auto text-xs text-gray-500 hover:text-gray-900 inline-flex items-center gap-1"
          @click="refreshRemotes"
        >
          <RefreshCw class="w-3 h-3" />
          Refresh
        </button>
      </div>

      <p v-if="!names.length" class="bm-card p-5 text-xs text-gray-500">
        No connection registered yet. <em>New connection</em> adds one, for notebooks to dispatch their acquisitions to.
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
            <p class="lx-mono text-gray-500 truncate">{{ describeRemote(state.remotes[name]) }}</p>
          </div>
          <router-link
            v-if="reportsServer(name)"
            :to="{ name: 'processes', query: { process: reportsServer(name).id } }"
            class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-medium hover:bg-emerald-100 transition"
            title="Its report server, in Running"
          >reports running</router-link>

          <div class="ml-auto flex flex-wrap items-center gap-1.5">
            <!-- The outputs of its runs: a report server on the same channel, read in the dashboard. -->
            <button
              type="button"
              class="lx-primary !py-1"
              :disabled="startingReports === name"
              :title="reportsServer(name)
                ? 'Open its reports in the dashboard'
                : 'Start a report server on the same machine, serving its reports folder, and open it in the dashboard'"
              @click="reports(name)"
            >
              <LayoutDashboard class="w-3.5 h-3.5" /> {{ startingReports === name ? 'Starting…' : 'Reports' }}
            </button>
            <button
              type="button"
              class="lx-action"
              :disabled="rebuilding === name"
              title="Delete its environment entirely, and create it again from qibocal and the requirements alone"
              @click="rebuild(name)"
            >
              <RefreshCw class="w-3.5 h-3.5" :class="{ 'lx-spin': rebuilding === name }" /> {{ rebuilding === name ? 'Regenerating…' : 'Regenerate env' }}
            </button>
            <button type="button" class="lx-action" title="Edit its options" @click="toggleEdit(name)">
              <Pencil class="w-3.5 h-3.5" /> Edit
            </button>
            <button type="button" class="lx-action" title="Open the form for a new connection with this one's options" @click="duplicate(name)">
              <Files class="w-3.5 h-3.5" /> Duplicate
            </button>
            <button type="button" class="lx-action" title="Forget this connection" @click="remove(name)">
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <form v-if="editing.name === name" class="mt-3.5 pt-3.5 border-t border-gray-100" @submit.prevent="saveEdit(name)">
          <notebook-fields
            :values="editing.form"
            :fields="REMOTE_FIELDS"
            :errors="edited.errors"
            :warnings="edited.warnings"
            named
            name-required
            name-help="What notebooks call it: Remote(connection=…), in remotes.json."
            :name-error="editNameError"
          />
          <div class="flex flex-wrap items-center gap-2 mt-4">
            <button type="submit" class="lx-primary" :disabled="editing.busy || !edited.valid || Boolean(editNameError)">Save</button>
            <button type="button" class="lx-action" @click="editing.name = null">Cancel</button>
          </div>
        </form>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bookmark, Files, LayoutDashboard, Pencil, Plus, RefreshCw, Trash2, X } from 'lucide-vue-next'
import NotebookFields from '../components/NotebookFields.vue'
import { confirmAction, desktop } from '../bridge.js'
import {
  state,
  attempt,
  notebookReportsServer,
  rebuildNotebook,
  refreshRemotes,
  startNotebookReports
} from '../state.js'
import { usePageKeys } from '../composables/pageKeys.js'
import {
  REMOTE_FIELDS,
  describeRemote,
  normalizeRemoteOptions,
  rebuildOptions,
  toRemoteEditorValues
} from '../lib/remotes.js'
import { blankEditor } from '../lib/notebooks.js'

const router = useRouter()

const creating = ref(false)
const saving = ref(false)
const form = reactive(blankEditor(REMOTE_FIELDS))
const editing = reactive({ name: null, form: blankEditor(REMOTE_FIELDS), busy: false })
const rebuilding = ref(null)
const startingReports = ref(null)

const names = computed(() => Object.keys(state.remotes || {}))
const created = computed(() => normalizeRemoteOptions(form))
const edited = computed(() => normalizeRemoteOptions(editing.form))

const newNameError = computed(() =>
  form.name && names.value.includes(form.name) ? `A connection named ${form.name} is registered already.` : ''
)
const editNameError = computed(() => {
  if (!editing.form.name) return 'A connection needs a name.'
  if (editing.form.name !== editing.name && names.value.includes(editing.form.name)) {
    return `A connection named ${editing.form.name} is registered already.`
  }
  return ''
})

/** Its report server is known by the connection, apart from notebook sessions of the same name. */
const reportsKey = name => `remote:${name}`
const reportsServer = name => notebookReportsServer(reportsKey(name))

const { focused } = usePageKeys({
  page: 'remotes',
  count: () => names.value.length,
  actions: {
    Enter: index => reports(names.value[index]),
    e: index => toggleEdit(names.value[index]),
    d: index => duplicate(names.value[index])
  }
})

async function register() {
  saving.value = true
  const saved = await attempt(() => desktop.saveRemote(form.name, created.value.options), `Connection ${form.name} registered.`, 'remotes')
  saving.value = false
  if (saved === undefined) return
  state.remotes = saved
  creating.value = false
  Object.assign(form, blankEditor(REMOTE_FIELDS))
}

function toggleEdit(name) {
  if (editing.name === name) {
    editing.name = null
    return
  }
  Object.assign(editing.form, toRemoteEditorValues(state.remotes[name]), { name })
  Object.assign(editing, { name, busy: false })
}

async function saveEdit(name) {
  editing.busy = true
  const renamed = editing.form.name
  const saved = await attempt(async () => {
    let current = await desktop.saveRemote(renamed, edited.value.options)
    if (renamed !== name) current = await desktop.removeRemote(name)
    return current
  }, `Connection ${renamed} saved.`, 'remotes')
  editing.busy = false
  if (saved === undefined) return
  state.remotes = saved
  editing.name = null
}

function duplicate(name) {
  Object.assign(form, toRemoteEditorValues(state.remotes[name]), { name: `${name} copy` })
  creating.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function reports(name) {
  const running = reportsServer(name)
  startingReports.value = name
  const options = state.remotes[name] || {}
  const started = await attempt(
    // Known by the connection, apart from a notebook session of the same name.
    () => startNotebookReports(options, name, { key: reportsKey(name) }),
    running ? null : `Starting the report server of ${name}; it appears in the dashboard once it answers.`,
    'processes'
  )
  startingReports.value = null
  if (started && !running) router.push({ name: 'processes' })
}

async function rebuild(name) {
  const venv = state.remotes[name]?.venv || 'qibocal'
  const confirmed = await confirmAction(
    `The environment "${venv}" of ${name} is deleted entirely, with everything installed in it, ` +
      'and created again from qibocal and the connection\'s requirements alone. This cannot be undone.',
    { title: 'Regenerate the environment', okLabel: 'Regenerate env' }
  )
  if (!confirmed) return
  rebuilding.value = name
  const started = await attempt(
    () => rebuildNotebook(rebuildOptions(state.remotes[name] || {})),
    `Regenerating the environment of ${name}; its output is in Running.`,
    'processes'
  )
  rebuilding.value = null
  if (started) router.push({ name: 'processes' })
}

async function remove(name) {
  const left = await attempt(() => desktop.removeRemote(name), `Connection ${name} removed.`, 'remotes')
  if (left === undefined) return
  state.remotes = left
  if (editing.name === name) editing.name = null
}

onMounted(() => refreshRemotes())
</script>
