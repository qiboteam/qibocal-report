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
      its own; pointing it elsewhere is for developers, and folded away.
    -->
    <section class="bm-card p-5">
      <h2 class="text-sm font-semibold text-gray-900 mb-3">Qibocal</h2>

      <div v-if="environment?.executable" class="flex flex-wrap items-center gap-x-4 gap-y-1 mb-4 text-xs">
        <span class="inline-flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span class="font-medium text-gray-800">{{ environment.version || 'available' }}</span>
        </span>
        <code class="lx-mono text-gray-500 truncate">{{ environment.executable }}</code>
        <span class="text-[11px] text-gray-400">{{ sourceLabel }}</span>
      </div>
      <p v-else-if="installing" class="text-xs text-gray-600 bg-[#f7f5ff] rounded-xl px-3 py-2 mb-4">
        Installing Qibocal: the progress is in <router-link to="/processes" class="text-[#833dff] hover:text-[#6b21a8]">Running</router-link>.
      </p>
      <p v-else class="text-xs text-amber-700 bg-amber-50 rounded-xl px-3 py-2 mb-4">
        Qibocal is not installed yet. The launcher can install it for you, in an environment of its own.
      </p>

      <p v-if="!environment?.python" class="text-xs text-red-700 bg-red-50 rounded-xl px-3 py-2 mb-4">
        No Python 3.10 or newer was found on this machine. Install one — from
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
          <Download class="w-3.5 h-3.5" /> {{ installing ? 'Installing…' : 'Install Qibocal' }}
        </button>
        <button
          v-else
          type="button"
          class="lx-action"
          :disabled="!environment?.python || installing"
          title="Bring the launcher's environment up to date"
          @click="install(true)"
        >
          <RefreshCw class="w-3.5 h-3.5" /> {{ installing ? 'Updating…' : 'Update' }}
        </button>
        <span class="lx-help !mt-0">
          <template v-if="environment?.managedReady">Installed in <code class="lx-mono">{{ environment.managed }}</code>.</template>
          <template v-else-if="environment?.python">With Python {{ environment.pythonVersion }}, into <code class="lx-mono">{{ environment.managed }}</code>.</template>
        </span>
      </div>

      <details class="lx-more">
        <summary><ChevronRight class="lx-chevron w-3.5 h-3.5" /> Developer options</summary>
        <div class="lx-more-body space-y-4">
          <p class="lx-help !mt-0">
            For a checkout of qibocal-report, or any environment that already has it: the choice made here wins over the
            launcher's own installation, until <em>Detect again</em>.
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

          <form-field
            v-slot="{ id }"
            label="Package to install"
            help="Default: qibocal-report"
            info="What goes into the launcher's own environment: a pinned version, a pre-release, or a different distribution. Several packages are separated by spaces. Applied on the next Install or Update."
          >
            <div class="flex items-center gap-2">
              <input :id="id" v-model.trim="packageDraft" type="text" class="lx-input lx-mono" @keydown.enter="savePackage" />
              <button type="button" class="lx-action shrink-0" :disabled="packageDraft === (environment?.package || '')" @click="savePackage">
                Save
              </button>
            </div>
          </form-field>

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
import { ChevronRight, Download, FolderOpen, RefreshCw, RotateCcw, Terminal, Trash2 } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import ConfigFile from '../components/ConfigFile.vue'
import FormField from '../components/FormField.vue'
import { chooseDirectory, chooseFile, desktop, openExternal, revealInFileManager } from '../bridge.js'
import {
  state,
  attempt,
  installQibocal,
  refreshConfigEntries,
  refreshEnvironment,
  refreshNotebooks,
  refreshPreferences,
  refreshServers
} from '../state.js'

const WEB_FRONTEND = 'https://qibo.science/qibocal-report'

const router = useRouter()
const chosen = ref([])
const platform = ref({ os: '—', arch: '' })
const packageDraft = ref('')

const environment = computed(() => state.environment)
const preferredExecutable = computed(() => state.preferences?.executable || null)
const installing = computed(() =>
  state.processes.some(process => process.kind === 'setup' && process.status === 'running')
)

const sourceLabel = computed(() => ({
  managed: 'the launcher\'s own installation',
  preference: 'chosen in the developer options',
  environment: 'from QIBOCAL_EXECUTABLE',
  path: 'found on the PATH',
  'well-known': 'found in a usual place'
})[environment.value?.source] || '')

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

async function savePackage() {
  const { package: _current, ...rest } = state.preferences || {}
  const settings = packageDraft.value ? { ...rest, package: packageDraft.value } : rest
  const saved = await attempt(() => desktop.savePreferences(settings), 'Package saved; it applies on the next Install or Update.')
  if (saved === undefined) return
  state.preferences = saved
  await refreshEnvironment()
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

watch(() => environment.value?.package, value => {
  packageDraft.value = value || ''
}, { immediate: true })

onMounted(async () => {
  await Promise.all([refreshEnvironment(), refreshConfigEntries(), refreshPreferences()])
  platform.value = (await attempt(() => desktop.platform())) || platform.value
})
</script>
