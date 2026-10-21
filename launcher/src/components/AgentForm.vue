<!--
  The settings of an agent configuration: where it is kept — this machine's
  agent.json, or an access node it is pushed to — its name, and the settings
  qibocal-agent reads, the few that matter first and the rest behind
  "More options". The same form for a new configuration and for editing one.
-->
<template>
  <div class="space-y-4">
    <div class="grid gap-4 sm:grid-cols-2">
      <form-field class="sm:col-span-2" label="Kept for" :help="form.host === 'local' ? 'An assistant, or autonomous runs, on this machine.' : 'An assistant on that machine: kept here, and pushed to its agent.json.'">
        <segmented-control v-model="form.host" :options="places" />
      </form-field>
      <form-field v-if="form.host !== 'local'" v-slot="{ id }" label="SSH destination of that machine" required>
        <input :id="id" v-model.trim="form.hostName" type="text" class="lx-input lx-mono" placeholder="access-node" spellcheck="false" autocomplete="off" autocapitalize="off" />
      </form-field>
      <form-field
        v-slot="{ id }"
        label="Name"
        :required="form.host !== 'local'"
        :help="form.host === 'local' ? 'Empty: the unnamed defaults.' : 'What the assistant there selects.'"
        :error="nameError"
      >
        <input :id="id" v-model.trim="form.name" type="text" class="lx-input lx-mono" placeholder="tuna" spellcheck="false" autocomplete="off" autocapitalize="off" />
      </form-field>
    </div>
    <notebook-fields :values="form" :fields="fields" :errors="errors" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import FormField from './FormField.vue'
import NotebookFields from './NotebookFields.vue'
import SegmentedControl from './SegmentedControl.vue'
import { AGENT_FIELDS, AGENT_NAME, agentEntry } from '../lib/agents.js'

const props = defineProps({
  form: { type: Object, required: true },
  /** The names already used where this one is kept. */
  names: { type: Array, default: () => [] }
})

const places = [
  { value: 'local', label: 'This machine' },
  { value: 'remote', label: 'Another machine' }
]

/** The fields, lists shown as text areas; the objective only on a named configuration. */
const fields = computed(() => AGENT_FIELDS
  .filter(field => !field.named || props.form.name)
  .map(field => (field.type === 'list' ? { ...field, type: 'textarea' } : field)))
const errors = computed(() => agentEntry(props.form, { named: Boolean(props.form.name) }).errors)
const nameError = computed(() => {
  const name = props.form.name
  if (!name) return props.form.host !== 'local' ? 'A configuration for another machine needs a name.' : ''
  if (!AGENT_NAME.test(name)) return 'A letter or digit, then letters, digits, underscores or hyphens.'
  if (props.names.includes(name)) return `${name} is used already there.`
  return ''
})
</script>
