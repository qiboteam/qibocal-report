<!--
  The settings of an agent configuration: where it is kept — this machine's
  agents.json, or one of the SSH remotes it is pushed to — its name, and the
  settings qibocal-agent reads, the few that matter first and the rest behind
  "More options". The same form for a new configuration and for editing one.
-->
<template>
  <div class="space-y-4">
    <div class="grid gap-4 sm:grid-cols-2">
      <form-field
        class="sm:col-span-2"
        label="Kept for"
        :help="form.host === 'local'
          ? 'An assistant, or autonomous runs, on this machine; it may still start the calibration server elsewhere, through its SSH destination.'
          : 'An assistant running on that remote: kept here, and pushed to its agents.json.'"
      >
        <segmented-control v-model="form.host" :options="places" />
      </form-field>
      <form-field
        v-if="form.host !== 'local'"
        v-slot="{ id, control }"
        label="Remote"
        required
        :help="remotes.length ? 'Where the assistant runs, among the remotes in Setup.' : 'Add the remote first, in Setup above.'"
      >
        <select :id="id" v-model="form.hostName" :class="['lx-select w-full', control]">
          <option value="" disabled>Choose a remote</option>
          <option v-for="remote in remotes" :key="remote.name" :value="remote.name">{{ remote.name }} — {{ remote.ssh }}</option>
        </select>
      </form-field>
      <form-field
        v-slot="{ id, control }"
        label="Name"
        required
        help="What runs and assistants select; default is the one used without a name."
        :error="nameError"
      >
        <input :id="id" v-model.trim="form.name" type="text" :class="['lx-input lx-mono', control]" placeholder="tuna" spellcheck="false" autocomplete="off" autocapitalize="off" />
      </form-field>
    </div>
    <notebook-fields :values="form" :fields="fields" :errors="errors" :choices="{ ssh: remotes.map(remote => remote.ssh) }" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import FormField from './FormField.vue'
import NotebookFields from './NotebookFields.vue'
import SegmentedControl from './SegmentedControl.vue'
import { AGENT_FIELDS, agentEntry, agentNameError } from '../lib/agents.js'

const props = defineProps({
  form: { type: Object, required: true },
  /** The names already used where this one is kept. */
  names: { type: Array, default: () => [] },
  /** The SSH remotes, `{ name, ssh }`: where a configuration is kept, and what its SSH destination offers. */
  remotes: { type: Array, default: () => [] }
})

const places = [
  { value: 'local', label: 'This machine' },
  { value: 'remote', label: 'A remote' }
]

/** The fields, lists shown as text areas. */
const fields = AGENT_FIELDS.map(field => (field.type === 'list' ? { ...field, type: 'textarea' } : field))
const errors = computed(() => agentEntry(props.form).errors)
const nameError = computed(() => {
  const name = props.form.name
  if (props.names.includes(name)) return `${name} is used already there.`
  return agentNameError(name)
})
</script>
