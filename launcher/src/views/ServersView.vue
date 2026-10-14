<template>
  <div class="max-w-4xl mx-auto px-5 py-8 space-y-5">
    <div>
      <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Servers</h1>
      <p class="mt-1 text-xs text-gray-500">
        A report server runs here, on another machine over SSH, or is already running somewhere you can reach.
      </p>
    </div>

    <!--
      One form for every new server. Where it runs decides which fields make
      sense; starting it for a look is the default, registering it a choice.
    -->
    <section class="bm-card p-5">
      <div class="flex flex-wrap items-center gap-3 mb-4">
        <h2 class="text-sm font-semibold text-gray-900">New server</h2>
        <segmented-control v-model="where" :options="places" class="ml-auto" />
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <form-field
          v-slot="{ id }"
          label="Name"
          help="How the server is listed here and in the dashboard."
        >
          <input
            :id="id"
            v-model="form.name"
            type="text"
            class="lx-input"
            :placeholder="suggested"
            @input="nameTouched = true"
          />
        </form-field>

        <!-- This machine -->
        <template v-if="where === 'local'">
          <form-field label="Mode" :help="modeHelp">
            <segmented-control v-model="form.mode" :options="modes" />
          </form-field>

          <form-field
            v-if="form.mode !== 'client'"
            v-slot="{ id }"
            class="sm:col-span-2"
            label="Reports directory"
            help="The folder holding the calibration runs. Left empty, the shared reports directory is served — ~/.local/share/qibocal/reports, created when missing."
          >
            <path-picker
              :id="id"
              v-model="form.directory"
              title="Choose the reports directory"
              placeholder="shared reports directory"
            />
          </form-field>

          <form-field v-slot="{ id }" label="Host">
            <input :id="id" v-model.trim="form.host" type="text" class="lx-input lx-mono" placeholder="localhost" />
          </form-field>

          <form-field v-slot="{ id }" label="Port" :error="errors.port">
            <div class="flex items-center gap-2">
              <input :id="id" v-model="form.port" type="number" min="1" max="65535" class="lx-input lx-mono" />
              <button
                type="button"
                class="shrink-0 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-[#ebe0ff] text-[#3b107e] hover:bg-[#dfceff] transition"
                title="Pick a port nobody is listening on"
                @click="pickFreePort"
              >
                Free port
              </button>
            </div>
          </form-field>

          <form-field v-if="form.mode === 'dev'" v-slot="{ id }" label="Frontend port" help="Where Vite serves the live interface.">
            <input :id="id" v-model="form.frontendPort" type="number" min="1" max="65535" class="lx-input lx-mono" />
          </form-field>
        </template>

        <!-- Another machine -->
        <template v-else-if="where === 'ssh'">
          <form-field
            v-slot="{ id }"
            label="SSH destination"
            help="SSH options followed by a host or user@host, as ssh takes them."
            :error="errors.ssh"
          >
            <input :id="id" v-model.trim="form.ssh" type="text" class="lx-input lx-mono" placeholder="user@login-node" />
          </form-field>

          <form-field
            v-slot="{ id }"
            class="sm:col-span-2"
            label="Reports directory"
            help="A path on that machine. Left empty, its shared reports directory is served — ~/.local/share/qibocal/reports there, created when missing."
          >
            <input :id="id" v-model.trim="form.directory" type="text" class="lx-input lx-mono" placeholder="shared reports directory" />
          </form-field>

          <form-field
            v-for="field in remoteFields"
            :key="field.name"
            v-slot="{ id }"
            :class="field.wide ? 'sm:col-span-2' : ''"
            :label="field.label"
            :help="field.help"
          >
            <input :id="id" v-model.trim="form[field.name]" type="text" class="lx-input lx-mono" :placeholder="field.placeholder" />
          </form-field>
        </template>

        <!-- Already running -->
        <form-field
          v-else
          v-slot="{ id }"
          label="Address"
          help="Any reachable Qibocal report server."
          :error="errors.url"
        >
          <input :id="id" v-model.trim="form.url" type="text" class="lx-input lx-mono" placeholder="https://reports.example.org" />
        </form-field>

        <div v-if="where !== 'reachable' && form.mode !== 'client'" class="flex items-end sm:col-span-2">
          <toggle-switch
            v-model="form.auth"
            label="User accounts"
            help="Enables authentication and issues an administrator invitation."
          />
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2.5 mt-5">
        <template v-if="where === 'reachable'">
          <button type="button" class="lx-primary" :disabled="!form.url" @click="register">
            Register
          </button>
          <span class="lx-help !mt-0">Nothing is started: the address is added to the servers the dashboard knows.</span>
        </template>
        <template v-else>
          <button type="button" class="lx-primary" :disabled="starting" @click="launch(false)">
            {{ starting ? 'Starting…' : 'Start' }}
          </button>
          <button
            type="button"
            class="lx-action"
            :disabled="starting"
            title="Start it, and keep it in servers.json for next time"
            @click="launch(true)"
          >
            <Bookmark class="w-3.5 h-3.5" /> Start and register
          </button>
          <span class="lx-mono text-gray-400 truncate">{{ preview }}</span>
        </template>
      </div>
    </section>

    <!-- Started for a look: around only while they run -->
    <section v-if="temporary.length" class="space-y-2.5">
      <div class="flex items-center gap-2 px-1">
        <h2 class="text-sm font-semibold text-gray-900">Running, not registered</h2>
        <span class="text-xs text-gray-400">{{ temporary.length }}</span>
      </div>
      <article v-for="process in temporary" :key="process.id" class="bm-card p-4 flex flex-wrap items-center gap-x-3 gap-y-1">
        <div class="min-w-0">
          <p class="text-sm font-medium text-gray-900 truncate">{{ process.label }}</p>
          <p class="lx-mono text-gray-500 truncate">{{ process.url }}</p>
        </div>
        <div class="ml-auto flex flex-wrap items-center gap-1.5">
          <button type="button" class="lx-action" @click="openDashboard(process.url)">
            <LayoutDashboard class="w-3.5 h-3.5" /> Open
          </button>
          <button type="button" class="lx-action" title="Keep it in servers.json" @click="keep(process)">
            <Bookmark class="w-3.5 h-3.5" /> Register
          </button>
          <button type="button" class="lx-action" title="Open in the browser" @click="openExternal(process.url)">
            <ExternalLink class="w-3.5 h-3.5" />
          </button>
        </div>
      </article>
    </section>

    <!-- Registered servers -->
    <section class="space-y-2.5">
      <div class="flex items-center gap-2 px-1">
        <h2 class="text-sm font-semibold text-gray-900">Registered servers</h2>
        <span class="text-xs text-gray-400">{{ state.servers.length }}</span>
        <button
          type="button"
          class="ml-auto text-xs text-gray-500 hover:text-gray-900 inline-flex items-center gap-1"
          @click="refreshServers"
        >
          <RefreshCw class="w-3 h-3" />
          Refresh
        </button>
      </div>

      <p v-if="!state.servers.length" class="bm-card p-5 text-xs text-gray-500">
        No server registered yet. Starting one with <em>Start and register</em>, or registering a reachable address, adds it here.
      </p>

      <article v-for="server in state.servers" :key="server.id" class="bm-card p-4">
        <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
          <div class="min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">{{ server.name || server.url }}</p>
            <p class="lx-mono text-gray-500 truncate">{{ server.url }}</p>
          </div>
          <span
            v-if="processFor(server)"
            class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-medium"
          >running here</span>

          <div class="ml-auto flex flex-wrap items-center gap-1.5">
            <button type="button" class="lx-action" @click="openDashboard(server.url)">
              <LayoutDashboard class="w-3.5 h-3.5" /> Open
            </button>
            <button
              v-if="!processFor(server) && recallLaunch(server.url)"
              type="button"
              class="lx-action"
              title="Start it again with the options used last time"
              @click="relaunch(server)"
            >
              <Play class="w-3.5 h-3.5" /> Start
            </button>
            <button type="button" class="lx-action" title="Re-issue an administrator invitation" @click="toggleInvite(server)">
              <KeyRound class="w-3.5 h-3.5" /> Invite
            </button>
            <button type="button" class="lx-action" title="Open in the browser" @click="openExternal(server.url)">
              <ExternalLink class="w-3.5 h-3.5" />
            </button>
            <button type="button" class="lx-action" title="Forget this server" @click="forget(server)">
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <!-- Administrator invitation -->
        <div v-if="invite.serverId === server.id" class="mt-3.5 pt-3.5 border-t border-gray-100 grid gap-3 sm:grid-cols-[1fr_auto_auto] sm:items-end">
          <form-field v-slot="{ id }" label="Administrator" help="Leave empty for the initial, unregistered administrator.">
            <input
              :id="id"
              v-model.trim="invite.username"
              type="text"
              class="lx-input"
              list="launcher-administrators"
              placeholder="username"
            />
          </form-field>
          <form-field v-slot="{ id }" label="Valid for" help="Hours.">
            <input :id="id" v-model="invite.hours" type="number" min="1" class="lx-input lx-mono w-24" />
          </form-field>
          <button type="button" class="lx-primary py-2" :disabled="invite.busy" @click="createInvite(server)">
            {{ invite.busy ? 'Working…' : 'Create link' }}
          </button>

          <div v-if="invite.result" class="sm:col-span-3 flex items-center gap-2 bg-[#f7f5ff] rounded-xl px-3 py-2">
            <code class="lx-mono flex-1 truncate text-[#3b107e]">{{ invite.result.invite_url }}</code>
            <span class="text-[11px] text-gray-500 shrink-0">
              {{ invite.result.expires_at ? `until ${invite.result.expires_at}` : 'no expiry' }}
            </span>
            <button type="button" class="lx-action shrink-0" @click="copy(invite.result.invite_url)">
              <Copy class="w-3.5 h-3.5" /> Copy
            </button>
          </div>
        </div>
      </article>

      <datalist id="launcher-administrators">
        <option v-for="user in administrators" :key="user.id || user.username" :value="user.username" />
      </datalist>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bookmark, Copy, ExternalLink, KeyRound, LayoutDashboard, Play, RefreshCw, Trash2 } from 'lucide-vue-next'
import FormField from '../components/FormField.vue'
import PathPicker from '../components/PathPicker.vue'
import SegmentedControl from '../components/SegmentedControl.vue'
import ToggleSwitch from '../components/ToggleSwitch.vue'
import { desktop, openExternal } from '../bridge.js'
import {
  state,
  attempt,
  fail,
  notify,
  openDashboard,
  recallLaunch,
  refreshServers,
  registerServer,
  forgetServer,
  runningServers,
  startServer,
  unregisteredServers
} from '../state.js'
import { serverCommand, serverUrl, suggestServerName } from '../lib/servers.js'

const route = useRoute()
const router = useRouter()

const places = [
  { value: 'local', label: 'This machine', help: 'Run qibocal here.' },
  { value: 'ssh', label: 'Another machine', help: 'Reach a host over SSH, prepare an environment there, and tunnel the server back.' },
  { value: 'reachable', label: 'Already running', help: 'Register an address, starting nothing.' }
]

const modes = [
  { value: 'server', label: 'Reports', help: 'Serve a directory of calibration runs.' },
  { value: 'dev', label: 'Developer', help: 'Live interface with hot reloading.' },
  { value: 'client', label: 'Client', help: 'Browse other servers, serving none.' }
]

// Worded like the matching notebook options, which describe the same things.
const remoteFields = [
  {
    name: 'venv',
    label: 'Server environment',
    placeholder: 'qibocal',
    help: 'Environment name or path on the remote host. It is created when missing.'
  },
  {
    name: 'workdir',
    label: 'Working directory',
    placeholder: '/shared/calibration',
    help: 'Directory the server starts from on the remote host.'
  },
  {
    name: 'install',
    label: 'Package to install',
    wide: true,
    placeholder: 'qibocal-report',
    help: 'Installed in the environment when it does not already provide qibocal.'
  }
]

const where = ref('local')
const form = reactive({
  name: '',
  mode: 'server',
  directory: '',
  host: 'localhost',
  port: 8000,
  auth: false,
  frontendPort: 5173,
  ssh: '',
  venv: '',
  workdir: '',
  install: '',
  url: ''
})
const nameTouched = ref(false)
const invite = reactive({ serverId: null, username: '', hours: 24, busy: false, result: null })
const administrators = ref([])
const starting = ref(false)

const temporary = computed(() => unregisteredServers())

/** The next free "Server N", counting registered and running ones alike. */
const suggested = computed(() =>
  suggestServerName([
    ...state.servers.map(server => server.name),
    ...runningServers().map(process => process.label)
  ])
)
const modeHelp = computed(() => modes.find(mode => mode.value === form.mode)?.help || '')

const errors = computed(() => {
  const found = {}
  if (where.value === 'ssh' && !form.ssh.trim()) {
    found.ssh = 'Name the machine to reach, as ssh would.'
  }
  if (where.value === 'reachable' && form.url && !serverUrl(form.url)) {
    found.url = 'Enter the address of the report server.'
  }
  const port = Number(form.port)
  if (where.value === 'local' && (!Number.isInteger(port) || port < 1 || port > 65535)) {
    found.port = 'Enter a port between 1 and 65535.'
  }
  return found
})

const preview = computed(() => serverCommand(launchOptions(false)))

function processFor(server) {
  const url = serverUrl(server.url)
  return state.processes.find(
    process => process.status === 'running' && process.url && serverUrl(process.url) === url
  )
}

async function pickFreePort() {
  const port = await attempt(() => desktop.freePort())
  if (port) form.port = port
}

/** Exactly what `start_server` receives, and what the preview describes. */
function launchOptions(register) {
  const away = where.value === 'ssh'
  const mode = away ? 'server' : form.mode
  return {
    mode,
    name: form.name.trim() || suggested.value,
    register,
    directory: mode === 'client' ? null : form.directory.trim() || null,
    host: form.host.trim() || 'localhost',
    port: Number(form.port),
    auth: form.auth,
    frontendPort: mode === 'dev' ? Number(form.frontendPort) : null,
    ssh: away ? form.ssh.trim() : null,
    venv: away ? form.venv.trim() || null : null,
    workdir: away ? form.workdir.trim() || null : null,
    install: away ? form.install.trim() || null : null
  }
}

async function launch(register) {
  const problem = Object.values(errors.value)[0]
  if (problem) {
    fail(problem)
    return
  }
  starting.value = true
  const options = launchOptions(register)
  try {
    await startServer(options)
    notify(
      options.ssh
        ? `Starting ${options.name} on ${options.ssh}; the tunnel address appears in Running.`
        : `Starting ${options.name} on http://${options.host}:${options.port}.`
    )
    // The next server gets the next name, unless one was chosen by hand.
    if (!nameTouched.value) form.name = ''
    // The command line registers the instance itself, once it is up.
    if (register) setTimeout(refreshServers, 1500)
    router.push({ name: 'processes' })
  } catch (error) {
    fail(error)
  } finally {
    starting.value = false
  }
}

async function relaunch(server) {
  const options = recallLaunch(server.url)
  if (!options) return
  const started = await attempt(
    () => startServer(options, { url: server.url }),
    `Starting ${server.name || server.url} again.`
  )
  if (started) router.push({ name: 'processes' })
}

async function register() {
  const problem = errors.value.url
  if (problem) {
    fail(problem)
    return
  }
  const name = form.name.trim() || suggested.value
  const added = await attempt(
    () => registerServer({ name, url: form.url, description: `Server at ${form.url}` }),
    `${name} registered.`
  )
  if (added) {
    form.url = ''
    if (!nameTouched.value) form.name = ''
  }
}

/** Keep a server that was started for a look. */
async function keep(process) {
  await attempt(
    () => registerServer({
      name: process.label,
      url: process.url,
      description: `Started by the launcher: ${process.detail}`
    }),
    `${process.label} registered.`
  )
}

async function forget(server) {
  await attempt(() => forgetServer(server.id), `${server.name || server.url} removed.`)
}

async function toggleInvite(server) {
  if (invite.serverId === server.id) {
    invite.serverId = null
    return
  }
  Object.assign(invite, { serverId: server.id, username: '', hours: 24, busy: false, result: null })
  if (!administrators.value.length) {
    administrators.value = (await attempt(() => desktop.administrators())) || []
  }
}

async function createInvite(server) {
  invite.busy = true
  invite.result = null
  try {
    invite.result = await desktop.reissueInvite({
      username: invite.username || null,
      serverUrl: server.url,
      expiresInHours: Number(invite.hours) || 24
    })
    notify('Invitation link created.')
  } catch (error) {
    fail(error)
  } finally {
    invite.busy = false
  }
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    notify('Link copied.')
  } catch (error) {
    fail(error)
  }
}

/** Jumping here from the system menu preselects the server to start. */
function applyQuery() {
  const server = state.servers.find(entry => entry.id === route.query.server)
  if (!server) return
  const remembered = recallLaunch(server.url)
  if (!remembered) return
  // Whether it was registered is settled: the server is in the list.
  const { register: _registered, ...options } = remembered
  Object.assign(form, {
    ...options,
    name: remembered.name || server.name || '',
    directory: remembered.directory || '',
    frontendPort: remembered.frontendPort || 5173,
    ssh: remembered.ssh || '',
    venv: remembered.venv || '',
    workdir: remembered.workdir || '',
    install: remembered.install || ''
  })
  nameTouched.value = Boolean(form.name)
  where.value = remembered.ssh ? 'ssh' : 'local'
}

onMounted(() => {
  refreshServers()
  applyQuery()
})
watch(() => route.query.server, applyQuery)
</script>
