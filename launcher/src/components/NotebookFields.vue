<!--
  The options of a notebook session: the few that matter first, the rest
  behind "More options" with their defaults. The same form for a new session
  and for editing a saved one, as ServerFields is for the servers.
-->
<template>
  <div>
    <div class="grid gap-4 sm:grid-cols-2">
      <!-- Where it runs, as for a server: it decides which fields make sense. -->
      <form-field v-if="'where' in values" class="sm:col-span-2" label="Where it runs" :help="placeHelp">
        <segmented-control v-model="values.where" :options="places" />
      </form-field>
      <form-field
        v-if="named"
        v-slot="{ id }"
        class="sm:col-span-2"
        label="Name"
        :required="nameRequired"
        :help="nameHelp"
        :error="nameError"
      >
        <input spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off"
          :id="id"
          v-model.trim="values.name"
          type="text"
          class="lx-input"
          placeholder="mychip"
        />
      </form-field>
      <form-field
        v-for="field in primaryFields"
        v-slot="{ id }"
        :key="field.name"
        :label="field.label"
        :help="field.help"
        :info="field.info"
        :error="errors[field.name]"
        :warning="warnings[field.name]"
      >
        <segmented-control
          v-if="field.type === 'choice'"
          v-model="values[field.name]"
          :options="field.options"
        />
        <select v-else-if="field.type === 'select'" :id="id" v-model="values[field.name]" class="lx-select w-full">
          <option value="">None</option>
          <option v-for="choice in choices[field.name] || []" :key="choice" :value="choice">{{ choice }}</option>
          <option v-if="values[field.name] && !(choices[field.name] || []).includes(values[field.name])" :value="values[field.name]">{{ values[field.name] }} (not offered here)</option>
        </select>
        <input spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off"
          v-else
          :id="id"
          v-model.trim="values[field.name]"
          type="text"
          class="lx-input lx-mono"
          :placeholder="field.placeholder"
        />
      </form-field>
    </div>

    <details class="lx-more">
      <summary><ChevronRight class="lx-chevron w-3.5 h-3.5" /> More options</summary>
      <div class="lx-more-body grid gap-4 sm:grid-cols-2">
        <form-field
          v-for="field in advancedFields"
          v-slot="{ id }"
          :key="field.name"
          :class="field.type === 'textarea' ? 'sm:col-span-2' : ''"
          :label="field.label"
          :help="field.help"
          :info="field.info"
          :error="errors[field.name]"
          :warning="warnings[field.name]"
        >
          <segmented-control
            v-if="field.type === 'choice'"
            v-model="values[field.name]"
            :options="field.options"
          />
          <textarea spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off"
            v-else-if="field.type === 'textarea'"
            :id="id"
            v-model="values[field.name]"
            rows="4"
            class="lx-input lx-mono"
            :placeholder="field.placeholder"
          />
          <div v-else-if="field.type === 'number'" class="flex items-center gap-2">
            <input :id="id" v-model="values[field.name]" type="number" min="1" class="lx-input lx-mono" />
            <span class="text-[11px] text-gray-400 shrink-0">{{ field.unit }}</span>
          </div>
          <path-picker
            v-else-if="field.name === 'workdir' && !values.ssh"
            :id="id"
            v-model="values[field.name]"
            title="Choose the working directory"
          />
          <input spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off"
            v-else
            :id="id"
            v-model.trim="values[field.name]"
            type="text"
            class="lx-input lx-mono"
            :placeholder="field.placeholder"
          />
        </form-field>
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
import { NOTEBOOK_FIELDS, NOTEBOOK_PLACES, fieldApplies } from '../lib/notebooks.js'

const props = defineProps({
  /** The editor values: every option, and `name` when `named`. */
  values: { type: Object, required: true },
  errors: { type: Object, default: () => ({}) },
  warnings: { type: Object, default: () => ({}) },
  /** Show the name field. */
  named: { type: Boolean, default: false },
  nameRequired: { type: Boolean, default: false },
  nameError: { type: String, default: '' },
  /** The options to show: a notebook session's, or another set described the same way. */
  fields: { type: Array, default: () => NOTEBOOK_FIELDS },
  nameHelp: { type: String, default: 'What the session is saved as, in notebooks.json.' },
  /** The options of `select` fields, by field name. */
  choices: { type: Object, default: () => ({}) },
  /** The places to choose from, when the values carry one. */
  places: { type: Array, default: () => NOTEBOOK_PLACES }
})

const applies = field => fieldApplies(field, props.values.where)
const primaryFields = computed(() => props.fields.filter(field => !field.advanced && applies(field)))
const advancedFields = computed(() => props.fields.filter(field => field.advanced && applies(field)))
const placeHelp = computed(() => props.places.find(place => place.value === props.values.where)?.help || '')
</script>
