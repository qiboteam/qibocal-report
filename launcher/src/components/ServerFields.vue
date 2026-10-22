<!--
  The fields that describe a server: where it runs, and how it is started
  there. The same component serves the registration form and the form behind
  "Edit", so a registered server can be changed in every respect it was
  registered with — the SSH destination included.

  `form` is the view's own reactive object, written in place; `where` is a
  model of its own, since it decides which fields make sense; `entry` marks
  the form of a registered server, which has a description and an address
  whatever the place.
-->
<template>
  <div class="space-y-4">
    <div class="grid gap-4 sm:grid-cols-2">
      <form-field class="sm:col-span-2" label="Where it runs" :help="placeHelp">
        <segmented-control :model-value="where" :options="places" @update:model-value="$emit('update:where', $event)" />
      </form-field>

      <form-field
        v-slot="{ id }"
        label="Name"
        :help="entry ? '' : 'Generated like the command line generates them; change it freely.'"
      >
        <input spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off" :id="id" v-model="form.name" type="text" class="lx-input" />
      </form-field>

      <form-field v-if="entry" v-slot="{ id }" label="Description" help="Shown under the name in the dashboard.">
        <input :id="id" v-model.trim="form.description" type="text" class="lx-input" />
      </form-field>

      <!-- This machine -->
      <template v-if="where === 'local'">
        <form-field label="Mode" :help="modeHelp">
          <segmented-control v-model="form.mode" :options="modes" />
        </form-field>

        <form-field
          v-if="entry"
          v-slot="{ id, control }"
          label="Address"
          required
          help="What the dashboard connects to; it follows the host and port below."
          :error="errors.url"
        >
          <input spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off" :id="id" v-model.trim="form.url" type="text" :class="['lx-input lx-mono', control]" />
        </form-field>

        <form-field
          v-slot="{ id }"
          class="sm:col-span-2"
          label="Reports directory"
          help="Default: the shared reports directory."
          :info="`The folder holding the calibration runs. Left empty, ${SHARED_DIRECTORY} is served, and created when it is not there yet.`"
        >
          <path-picker :id="id" v-model="form.directory" title="Choose the reports directory" />
        </form-field>
      </template>

      <!-- Another machine -->
      <template v-else-if="where === 'ssh'">
        <form-field
          v-slot="{ id, control }"
          label="SSH destination"
          required
          info="SSH options followed by a host or user@host, the way ssh takes them. Host aliases, agent authentication and jump hosts from the SSH configuration all work; the destination comes last."
          :error="errors.ssh"
        >
          <input spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off" :id="id" v-model.trim="form.ssh" type="text" :class="['lx-input lx-mono', control]" placeholder="user@host" :list="`${id}-machines`" />
          <!-- The machines, offered by destination, each named. -->
          <datalist :id="`${id}-machines`">
            <option v-for="machine in machines" :key="machine.name" :value="machine.ssh" :label="machine.name" />
          </datalist>
        </form-field>

        <form-field
          v-slot="{ id }"
          label="Reports directory"
          help="Default: the shared reports directory of that machine."
          :info="`A path on that machine, typed rather than browsed, since the file dialog only sees this one. Left empty, ${SHARED_DIRECTORY} there is served, and created when missing.`"
        >
          <input spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off" :id="id" v-model.trim="form.directory" type="text" class="lx-input lx-mono" />
        </form-field>

        <form-field
          v-if="entry"
          v-slot="{ id, control }"
          label="Address"
          required
          help="The tunnel's end on this machine; it is renewed, and the entry moved, each time the server is started again."
          :error="errors.url"
        >
          <input spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off" :id="id" v-model.trim="form.url" type="text" :class="['lx-input lx-mono', control]" />
        </form-field>
      </template>

      <!-- Already running -->
      <form-field
        v-else
        v-slot="{ id, control }"
        label="Address"
        required
        info="Any reachable Qibocal report server. A bare host and port is accepted, and read as http."
        :error="errors.url"
      >
        <input spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off" :id="id" v-model.trim="form.url" type="text" :class="['lx-input lx-mono', control]" placeholder="https://host:port" />
      </form-field>
    </div>

    <!-- The optional settings, with their defaults -->
    <details v-if="where !== 'reachable'" class="lx-more">
      <summary><ChevronRight class="lx-chevron w-3.5 h-3.5" /> More options</summary>
      <div class="lx-more-body grid gap-4 sm:grid-cols-2">
        <template v-if="where === 'local'">
          <form-field v-slot="{ id }" label="Host" help="Default: localhost" info="The address the server binds to. 0.0.0.0 makes it reachable from other machines on the network.">
            <input spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off" :id="id" v-model.trim="form.host" type="text" class="lx-input lx-mono" />
          </form-field>

          <form-field v-slot="{ id }" label="Port" help="Default: 8000" :error="errors.port">
            <div class="flex items-center gap-2">
              <input :id="id" v-model="form.port" type="number" min="1" max="65535" class="lx-input lx-mono" />
              <button
                type="button"
                class="lx-action shrink-0"
                title="Pick a port nobody is listening on"
                @click="pickFreePort"
              >
                Free port
              </button>
            </div>
          </form-field>

          <form-field v-if="form.mode === 'dev'" v-slot="{ id }" label="Frontend port" help="Default: 5173" info="Where Vite serves the live interface.">
            <input :id="id" v-model="form.frontendPort" type="number" min="1" max="65535" class="lx-input lx-mono" />
          </form-field>
        </template>

        <template v-else>
          <form-field
            v-for="field in remoteFields"
            :key="field.name"
            v-slot="{ id }"
            :label="field.label"
            :help="field.help"
            :info="field.info"
          >
            <input spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off" :id="id" v-model.trim="form[field.name]" type="text" class="lx-input lx-mono" />
          </form-field>
        </template>

        <div class="flex items-end sm:col-span-2">
          <toggle-switch
            v-model="form.auth"
            label="User accounts"
            help="Off by default. On, users sign in, and an administrator invitation is issued at start."
          />
        </div>
      </div>
    </details>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChevronRight } from 'lucide-vue-next'
import FormField from './FormField.vue'
import PathPicker from './PathPicker.vue'
import SegmentedControl from './SegmentedControl.vue'
import ToggleSwitch from './ToggleSwitch.vue'
import { desktop } from '../bridge.js'
import { attempt, machines } from '../state.js'
import { PLACES, SHARED_DIRECTORY } from '../lib/servers.js'

const props = defineProps({
  form: { type: Object, required: true },
  where: { type: String, required: true },
  errors: { type: Object, default: () => ({}) },
  entry: { type: Boolean, default: false }
})
defineEmits(['update:where'])

const places = PLACES

const modes = [
  { value: 'server', label: 'Reports', help: 'Serve a directory of calibration runs.' },
  { value: 'dev', label: 'Developer', help: 'Live interface with hot reloading.' }
]

// Worded like the matching notebook options, which describe the same things.
const remoteFields = [
  {
    name: 'venv',
    label: 'Server environment',
    help: 'Default: qibocal-report',
    info: 'An environment name, resolved under ~/.cache/qibocal/envs on that machine, or an absolute path there. Created when missing, and given the package below when it has no qibocal-report — the rule the notebook sessions follow too.'
  },
  {
    name: 'workdir',
    label: 'Working directory',
    help: 'Default: a fresh temporary directory.',
    info: 'Where the server starts from on that machine. It writes nothing there, so the default keeps it out of the home folder; set it for relative paths.'
  },
  {
    name: 'install',
    label: 'Package to install',
    help: 'Default: the same qibocal-report as this launcher.',
    info: 'What goes into the environment when it has no qibocal: by default the very commit this launcher was built from, so the two agree; or a release, a pinned version, a different distribution.'
  }
]

const placeHelp = computed(() => {
  const place = places.find(entry => entry.value === props.where)
  if (!place) return ''
  // For a registered server, the third place means the launcher starts nothing.
  if (props.entry && place.value === 'reachable') return 'Registered only: the launcher does not start it.'
  return place.help
})
const modeHelp = computed(() => modes.find(mode => mode.value === props.form.mode)?.help || '')

async function pickFreePort() {
  const port = await attempt(() => desktop.freePort())
  if (port) props.form.port = port
}
</script>
