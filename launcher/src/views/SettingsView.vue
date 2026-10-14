<template>
  <div class="max-w-4xl mx-auto px-5 py-8 space-y-5">
    <div>
      <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Configuration</h1>
      <p class="mt-1 text-xs text-gray-500">
        The <code class="lx-mono">qibocal</code> command line the launcher drives, and the files it shares with it.
      </p>
    </div>

    <!--
      The launcher installs the command line itself, in an environment of
      its own, the first time something needs it; which version, and
      pointing it elsewhere, are developer options, folded away.
    -->
    <section class="bm-card p-5">
      <h2 class="text-sm font-semibold text-gray-900 mb-3">qibocal-report</h2>

      <div v-if="environment?.executable" class="flex flex-wrap items-center gap-x-4 gap-y-1 mb-4 text-xs">
        <span class="inline-flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span class="font-medium text-gray-800">{{ environment.version || 'available' }}</span>
          <span v-if="installedLabel" class="text-gray-500">· {{ installedLabel }}</span>
        </span>
        <code class="lx-mono text-gray-500 truncate">{{ environment.executable }}</code>
        <span class="text-[11px] text-gray-400">{{ sourceLabel }}</span>
      </div>
      <p v-else-if="installing" class="text-xs text-gray-700 bg-[#f7f5ff] rounded-xl px-3 py-2 mb-4 inline-flex items-center gap-2">
        <Loader2 class="w-3.5 h-3.5 lx-spin text-[#833dff]" />
        <span>Installing qibocal-report, {{ describeSpec(environment?.package, environment) }}: the progress is in
          <router-link to="/processes" class="text-[#833dff] hover:text-[#6b21a8]">Running</router-link>.</span>
      </p>
      <p v-else-if="environment?.python" class="text-xs text-amber-700 bg-amber-50 rounded-xl px-3 py-2 mb-4">
        qibocal-report is not installed. The launcher installs it the first time a server, a notebook or an invitation
        needs it; <em>Install qibocal-report</em> does it now. The output goes to
        <router-link to="/processes" class="hover:text-amber-900">Running</router-link>.
      </p>

      <p v-if="environment && !environment.python" class="text-xs text-red-700 bg-red-50 rounded-xl px-3 py-2 mb-4">
        No Python 3.10 or newer was found on this machine to install qibocal-report with. Install one — from
        <button type="button" class="text-[#833dff] hover:text-[#6b21a8]" @click="openExternal('https://www.python.org/downloads/')">python.org</button>
        or the system package manager — and come back: the launcher creates its environment with it.
      </p>

      <div class="flex flex-wrap items-center gap-2">
        <button
          v-if="!environment?.managedReady"
          type="button"
          class="lx-primary"
          :disabled="!environment?.python || installing"
          @click="install(false)"
        >
          <Loader2 v-if="installing" class="w-3.5 h-3.5 lx-spin" />
          <Download v-else class="w-3.5 h-3.5" />
          {{ installing ? 'Installing…' : 'Install qibocal-report' }}
        </button>
        <button
          v-else-if="switchable"
          type="button"
          class="lx-primary"
          :disabled="!environment?.python || installing"
          :title="`Replace ${installedLabel} with ${describeSpec(environment.package, environment)}`"
          @click="install(true)"
        >
          <Loader2 v-if="installing" class="w-3.5 h-3.5 lx-spin" />
          <RefreshCw v-else class="w-3.5 h-3.5" />
          {{ installing ? 'Switching…' : `Switch to ${describeSpec(environment.package, environment)}` }}
        </button>
        <button
          v-else
          type="button"
          class="lx-action"
          :disabled="!environment?.python || installing"
          title="Install the chosen version again, bringing it and its dependencies up to date"
          @click="install(true)"
        >
          <Loader2 v-if="installing" class="w-3.5 h-3.5 lx-spin" />
          <RefreshCw v-else class="w-3.5 h-3.5" />
          {{ installing ? 'Updating…' : 'Update' }}
        </button>
        <span class="lx-help !mt-0">
          <template v-if="environment?.managedReady">In <code class="lx-mono">{{ environment.managed }}</code>.</template>
          <template v-else-if="environment?.python">With Python {{ environment.pythonVersion }}, into <code class="lx-mono">{{ environment.managed }}</code>.</template>
        </span>
      </div>

      <details class="lx-more">
        <summary><ChevronRight class="lx-chevron w-3.5 h-3.5" /> Developer options</summary>
        <div class="lx-more-body space-y-4">
          <!-- Which qibocal-report goes into the launcher's environment -->
          <form-field
            v-slot="{ id }"
            label="Version"
            :help="versionHelp"
            info="A release from PyPI, or a commit, branch or tag of the repository installed from its archive, so no git is needed. The default is the commit this launcher was built from, whose command line takes exactly the options the launcher passes. The choice is kept in launcher.json and applied by Switch, Update, or the next installation."
          >
            <div class="flex items-center gap-2">
              <select :id="id" v-model="choice" class="lx-select" :disabled="installing">
                <optgroup v-if="grouped.commit.length" label="This build">
                  <option v-for="option in grouped.commit" :key="option.spec" :value="option.spec">{{ option.label }}</option>
                </optgroup>
                <optgroup v-if="grouped.release.length" label="Releases (PyPI)">
                  <option v-for="option in grouped.release" :key="option.spec" :value="option.spec">{{ option.label }}</option>
                </optgroup>
                <optgroup v-if="grouped.branch.length" label="Branches">
                  <option v-for="option in grouped.branch" :key="option.spec" :value="option.spec">{{ option.label }}</option>
                </optgroup>
                <optgroup v-if="grouped.tag.length" label="Tags">
                  <option v-for="option in grouped.tag" :key="option.spec" :value="option.spec">{{ option.label }}</option>
                </optgroup>
                <optgroup v-if="grouped.other.length" label="Other">
                  <option v-for="option in grouped.other" :key="option.spec" :value="option.spec">{{ option.label }}</option>
                </optgroup>
                <option :value="CUSTOM">Something else…</option>
              </select>
              <button type="button" class="lx-action shrink-0" title="Fetch the lists again" :disabled="fetching" @click="loadVersions">
                <Loader2 v-if="fetching" class="w-3.5 h-3.5 lx-spin" />
                <RefreshCw v-else class="w-3.5 h-3.5" />
              </button>
            </div>
          </form-field>

          <form-field
            v-if="choice === CUSTOM"
            v-slot="{ id }"
            label="Requirement"
            help="Anything pip install accepts."
            info="A pinned version, a pre-release, a Git URL, a local checkout — one requirement, as it would be typed after pip install."
          >
            <input :id="id" v-model.trim="custom" type="text" class="lx-input lx-mono" placeholder="qibocal-report==0.2.0" />
          </form-field>

          <div class="flex flex-wrap items-center gap-2">
            <button type="button" class="lx-action" :disabled="!dirty" @click="saveVersion">
              <Bookmark class="w-3.5 h-3.5" /> Save version
            </button>
            <span v-if="listsError" class="lx-warning !mt-0">{{ listsError }}</span>
          </div>

          <!-- Another environment altogether -->
          <div>
            <p class="lx-label">Another environment</p>
            <p class="lx-help !mt-0 mb-2">
              For a checkout of qibocal-report, or any environment that already has it: the choice wins over the
              launcher's own installation, until <em>Detect again</em>. The command line must take the options this
              launcher passes, as the current sources do.
            </p>
            <div class="flex flex-wrap items-center gap-2">
              <button type="button" class="lx-action" @click="pickExecutable(true)">
                <FolderOpen class="w-3.5 h-3.5" /> Choose environment…
              </button>
              <button type="button" class="lx-action" @click="pickExecutable(false)">
                <Terminal class="w-3.5 h-3.5" /> Choose executable…
              </button>
              <button v-if="preferredExecutable" type="button" class="lx-action" @click="clearExecutable">
                <RotateCcw class="w-3.5 h-3.5" /> Detect again
              </button>
            </div>
          </div>

          <details v-if="environment?.searched?.length">
            <summary class="text-[11px] text-gray-400 cursor-pointer select-none">Where the launcher looked</summary>
            <ul class="mt-2 space-y-0.5">
              <li v-for="place in environment.searched" :key="place" class="lx-mono text-gray-400 truncate">{{ place }}</li>
            </ul>
          </details>
        </div>
      </details>
    </section>

    <section class="space-y-2.5">
      <div class="flex flex-wrap items-center gap-2 px-1">
        <h2 class="text-sm font-semibold text-gray-900">Shared configuration</h2>
        <code class="lx-mono text-gray-400 truncate">{{ environment?.configDirectory }}</code>
        <button
          v-if="environment?.configDirectory"
          type="button"
          class="lx-action ml-auto"
          @click="reveal(environment.configDirectory)"
        >
          <FolderOpen class="w-3.5 h-3.5" /> Reveal
        </button>
      </div>

      <config-file
        v-for="entry in state.configEntries"
        :key="entry.name"
        :entry="entry"
        :selected="chosen.includes(entry.name)"
        @toggle="toggle"
        @saved="reload"
      />

      <div class="flex flex-wrap items-center gap-2 px-1 pt-1">
        <button type="button" class="lx-action" :disabled="!chosen.length" @click="removeChosen">
          <Trash2 class="w-3.5 h-3.5" /> Delete selected
        </button>
        <span class="lx-help !mt-0">
          Deleting <code class="lx-mono">auth.json</code> signs every user out and clears the administrators.
        </span>
      </div>
    </section>

    <section class="bm-card p-5">
      <h2 class="text-sm font-semibold text-gray-900 mb-3">About</h2>
      <dl class="grid gap-x-6 gap-y-1.5 sm:grid-cols-2 text-xs">
        <div class="flex gap-2">
          <dt class="text-gray-400 w-20 shrink-0">Platform</dt>
          <dd class="text-gray-800 lx-mono">{{ platform.os }} · {{ platform.arch }}</dd>
        </div>
        <div class="flex gap-2">
          <dt class="text-gray-400 w-20 shrink-0">Reports</dt>
          <dd>
            <button type="button" class="text-[#833dff] hover:text-[#6b21a8] transition" @click="openExternal(WEB_FRONTEND)">
              {{ WEB_FRONTEND }}
            </button>
          </dd>
        </div>
      </dl>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  Bookmark,
  ChevronRight,
  Download,
  FolderOpen,
  Loader2,
  RefreshCw,
  RotateCcw,
  Terminal,
  Trash2
} from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import ConfigFile from '../components/ConfigFile.vue'
import FormField from '../components/FormField.vue'
import { chooseDirectory, chooseFile, desktop, openExternal, revealInFileManager } from '../bridge.js'
import {
  state,
  attempt,
  installQibocal,
  installing,
  refreshConfigEntries,
  refreshEnvironment,
  refreshNotebooks,
  refreshPreferences,
  refreshServers
} from '../state.js'
import {
  BRANCHES_URL,
  PYPI_URL,
  TAGS_URL,
  defaultSpec,
  describeSpec,
  parseRefs,
  parseReleases,
  versionOptions
} from '../lib/versions.js'

const WEB_FRONTEND = 'https://qibo.science/qibocal-report'
/** The select value that reveals the free-text requirement. */
const CUSTOM = ' custom'

const router = useRouter()
const chosen = ref([])
const platform = ref({ os: '—', arch: '' })

const environment = computed(() => state.environment)
const preferredExecutable = computed(() => state.preferences?.executable || null)

const sourceLabel = computed(() => ({
  managed: 'the launcher\'s own installation',
  preference: 'chosen in the developer options',
  environment: 'from QIBOCAL_EXECUTABLE',
  path: 'found on the PATH',
  'well-known': 'found in a usual place'
})[environment.value?.source] || '')

/** What the managed environment holds, when that is what runs. */
const installedLabel = computed(() =>
  environment.value?.source === 'managed' && environment.value?.managedPackage
    ? describeSpec(environment.value.managedPackage, environment.value)
    : ''
)
/** The requirement that applies now: the chosen one, or this build's commit. */
const effective = computed(() => environment.value?.package || defaultSpec(environment.value))
/** The chosen version differs from the installed one: offer to switch. */
const switchable = computed(() =>
  Boolean(environment.value?.managedReady && environment.value?.managedPackage &&
    environment.value.managedPackage !== effective.value)
)

// --- The version picker -----------------------------------------------------

const releases = ref([])
const branches = ref([])
const tags = ref([])
const fetching = ref(false)
const listsError = ref('')
const choice = ref('')
const custom = ref('')

const options = computed(() =>
  versionOptions({
    releases: releases.value,
    branches: branches.value,
    tags: tags.value,
    current: effective.value,
    environment: environment.value
  })
)
const grouped = computed(() => {
  const groups = { commit: [], release: [], branch: [], tag: [], other: [] }
  for (const option of options.value) (groups[option.kind] || groups.other).push(option)
  return groups
})
const chosenSpec = computed(() => (choice.value === CUSTOM ? custom.value.trim() : choice.value))
const dirty = computed(() => Boolean(chosenSpec.value) && chosenSpec.value !== effective.value)
const versionHelp = computed(() => `Default: ${describeSpec(defaultSpec(environment.value), environment.value)}.`)

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: 'application/json' } })
  if (response.status === 404) return null
  if (!response.ok) throw new Error(`${url} answered ${response.status}.`)
  return response.json()
}

/** The lists behind the picker; a failure leaves the current choice usable. */
async function loadVersions() {
  fetching.value = true
  listsError.value = ''
  const results = await Promise.allSettled([fetchJson(PYPI_URL), fetchJson(BRANCHES_URL), fetchJson(TAGS_URL)])
  const [pypi, branchList, tagList] = results.map(result => (result.status === 'fulfilled' ? result.value : undefined))
  if (pypi !== undefined) releases.value = parseReleases(pypi)
  if (branchList !== undefined) branches.value = parseRefs(branchList)
  if (tagList !== undefined) tags.value = parseRefs(tagList)
  const failed = results.filter(result => result.status === 'rejected')
  if (failed.length) listsError.value = 'Some lists could not be fetched; the known versions are shown.'
  fetching.value = false
}

function syncChoice() {
  const current = effective.value
  if (options.value.some(option => option.spec === current)) {
    choice.value = current
  } else {
    choice.value = CUSTOM
    custom.value = current
  }
}

async function saveVersion() {
  const spec = chosenSpec.value
  if (!spec) return
  const { package: _current, ...rest } = state.preferences || {}
  const settings = spec === defaultSpec(environment.value) ? rest : { ...rest, package: spec }
  const saved = await attempt(() => desktop.savePreferences(settings), `Version saved: ${describeSpec(spec, environment.value)}.`)
  if (saved === undefined) return
  state.preferences = saved
  await refreshEnvironment()
}

// --- The rest ---------------------------------------------------------------

/** A saved file may hold servers, connections or preferences: refresh them all. */
async function reload() {
  await Promise.all([refreshConfigEntries(), refreshServers(), refreshNotebooks(), refreshPreferences()])
}

function toggle(name) {
  chosen.value = chosen.value.includes(name)
    ? chosen.value.filter(entry => entry !== name)
    : [...chosen.value, name]
}

async function install(upgrade) {
  const started = await attempt(() => installQibocal(upgrade))
  if (started) router.push({ name: 'processes' })
}

async function pickExecutable(directory) {
  const picked = await attempt(() =>
    directory
      ? chooseDirectory('Choose the environment holding qibocal')
      : chooseFile('Choose the qibocal executable')
  )
  if (!picked) return
  const updated = await attempt(() => desktop.setExecutable(picked), 'Qibocal installation updated.')
  if (!updated) return
  state.environment = updated
  await refreshPreferences()
}

async function clearExecutable() {
  const updated = await attempt(() => desktop.setExecutable(null), 'Back to the launcher\'s own installation.')
  if (!updated) return
  state.environment = updated
  await refreshPreferences()
}

async function removeChosen() {
  const names = [...chosen.value]
  const removed = await attempt(
    () => desktop.removeConfigEntries(names),
    files => (files.length ? `Removed ${files.length} file(s).` : 'Nothing to remove.')
  )
  if (removed === undefined) return
  chosen.value = []
  await reload()
}

async function reveal(path) {
  await attempt(() => revealInFileManager(path))
}

watch(effective, syncChoice, { immediate: true })

onMounted(async () => {
  await Promise.all([refreshEnvironment(), refreshConfigEntries(), refreshPreferences()])
  platform.value = (await attempt(() => desktop.platform())) || platform.value
  await loadVersions()
  syncChoice()
})
</script>
