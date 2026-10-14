<!--
  One shared configuration file, opened for editing.

  The file is shown as what it holds — servers, connections, preferences —
  with the JSON one toggle away for everything the entry editor cannot
  describe. Saving goes through the native side, which refuses anything that
  is not valid JSON and replaces the file in one step.
-->
<template>
  <section class="bm-card overflow-hidden">
    <header class="flex flex-wrap items-center gap-x-3 gap-y-1 p-4">
      <label class="flex items-center gap-2.5 cursor-pointer">
        <input
          type="checkbox"
          class="accent-[#833dff]"
          :disabled="!entry.exists"
          :checked="selected"
          @change="$emit('toggle', entry.name)"
        />
        <span>
          <span class="block text-sm font-medium text-gray-900">{{ entry.name }}</span>
          <span class="block lx-help !mt-0">{{ entry.description }}</span>
        </span>
      </label>

      <span class="ml-auto text-xs text-gray-400 whitespace-nowrap">
        {{ entry.exists ? size(entry.size) : 'not created' }}
      </span>
      <button type="button" class="lx-action" @click="toggleOpen">
        <component :is="open ? ChevronUp : ChevronDown" class="w-3.5 h-3.5" />
        {{ open ? 'Close' : 'Edit' }}
      </button>
    </header>

    <div v-if="open" class="border-t border-gray-100 p-4 space-y-3">
      <p v-if="shape.warning" class="text-xs text-red-700 bg-red-50 rounded-xl px-3 py-2">
        {{ shape.warning }}
      </p>
      <p v-if="loading" class="text-xs text-gray-500">Reading {{ entry.name }}…</p>
      <p v-else-if="error" class="text-xs text-red-700 bg-red-50 rounded-xl px-3 py-2">{{ error }}</p>

      <!-- A file that could not be structured has no value, only its text. -->
      <template v-if="!loading && (raw || value !== null)">
        <!-- Entries -->
        <div v-if="!raw" class="space-y-2">
          <p v-if="!entries.length" class="text-xs text-gray-500">
            No {{ shape.entry }} yet.
          </p>

          <article
            v-for="item in entries"
            :key="item.key"
            class="rounded-xl bg-[#fafafa]"
          >
            <div class="flex items-center gap-2 px-3 py-2">
              <button
                type="button"
                class="flex-1 min-w-0 text-left"
                @click="expanded = expanded === item.key ? null : item.key"
              >
                <span class="block text-xs font-medium text-gray-900 truncate">{{ item.title }}</span>
                <span class="block lx-mono text-gray-500 truncate">{{ item.subtitle }}</span>
              </button>
              <button type="button" class="lx-action" :title="`Remove this ${shape.entry}`" @click="remove(item.key)">
                <Trash2 class="w-3.5 h-3.5" />
              </button>
              <component
                :is="expanded === item.key ? ChevronUp : ChevronDown"
                class="w-3.5 h-3.5 text-gray-400 shrink-0"
              />
            </div>

            <div v-if="expanded === item.key" class="px-3 pb-3 pt-1 grid gap-3 sm:grid-cols-2">
              <form-field
                v-if="shape.kind === 'map'"
                v-slot="{ id }"
                class="sm:col-span-2"
                label="Name"
                help="How this entry is referred to everywhere else."
              >
                <input
                  :id="id"
                  class="lx-input lx-mono"
                  :value="item.key"
                  @change="rename(item.key, $event.target.value)"
                />
              </form-field>

              <form-field
                v-for="field in fieldsOf(item)"
                :key="`${item.key}:${field.name}`"
                v-slot="{ id }"
                :class="field.type === 'json' ? 'sm:col-span-2' : ''"
                :label="field.label"
                :help="field.help"
                :error="jsonErrors[`${item.key}:${field.name}`]"
              >
                <toggle-switch
                  v-if="field.type === 'boolean'"
                  label=""
                  :model-value="Boolean(field.value)"
                  @update:model-value="set(item.key, field.name, $event)"
                />
                <input
                  v-else-if="field.type === 'number'"
                  :id="id"
                  type="number"
                  class="lx-input lx-mono"
                  :value="field.value"
                  @change="set(item.key, field.name, number($event.target.value))"
                />
                <textarea
                  v-else-if="field.type === 'json'"
                  :id="id"
                  rows="4"
                  class="lx-input lx-mono"
                  :value="json(field.value)"
                  @input="setJson(item.key, field.name, $event.target.value)"
                />
                <input
                  v-else
                  :id="id"
                  type="text"
                  class="lx-input"
                  :class="{ 'lx-mono': field.mono }"
                  :value="field.value ?? ''"
                  @change="set(item.key, field.name, $event.target.value)"
                />
              </form-field>
            </div>
          </article>

          <button v-if="shape.template" type="button" class="lx-action" @click="add">
            <Plus class="w-3.5 h-3.5" /> Add a {{ shape.entry }}
          </button>
        </div>

        <!-- The file itself -->
        <div v-else>
          <textarea
            v-model="buffer"
            rows="14"
            spellcheck="false"
            class="lx-input lx-mono"
            :class="{ 'ring-2 ring-red-200': rawError }"
          />
          <p v-if="rawError" class="lx-error">{{ rawError }}</p>
        </div>
      </template>

      <div class="flex flex-wrap items-center gap-2 pt-1">
        <button type="button" class="lx-action" @click="toggleRaw">
          <Braces class="w-3.5 h-3.5" /> {{ raw ? `Back to the ${shape.entry}s` : 'Edit as JSON' }}
        </button>
        <button type="button" class="lx-action ml-auto" :disabled="!dirty" @click="load">
          <RotateCcw class="w-3.5 h-3.5" /> Revert
        </button>
        <button
          type="button"
          class="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-[#833dff] text-white hover:bg-[#722ce6] transition disabled:opacity-40"
          :disabled="!dirty || saving || Boolean(rawError)"
          @click="save"
        >
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Braces, ChevronDown, ChevronUp, Plus, RotateCcw, Trash2 } from 'lucide-vue-next'
import FormField from './FormField.vue'
import ToggleSwitch from './ToggleSwitch.vue'
import { desktop } from '../bridge.js'
import {
  addEntry,
  describeEntries,
  entryFields,
  formatDocument,
  parseDocument,
  removeEntry,
  renameEntry,
  shapeOf,
  updateEntry
} from '../lib/config.js'

const props = defineProps({
  entry: { type: Object, required: true },
  selected: { type: Boolean, default: false }
})
const emit = defineEmits(['toggle', 'saved'])

const open = ref(false)
const raw = ref(false)
const loading = ref(false)
const saving = ref(false)
const error = ref(null)
const expanded = ref(null)
/** The document as parsed, and as it was read: the difference is "dirty". */
const value = ref(null)
const original = ref('')
const buffer = ref('')
const jsonErrors = ref({})

const shape = computed(() => shapeOf(props.entry.name))
const entries = computed(() => describeEntries(props.entry.name, value.value))
const current = computed(() => (value.value === null ? '' : formatDocument(value.value)))
const dirty = computed(() => (raw.value ? buffer.value !== original.value : current.value !== original.value))
const rawError = computed(() => (raw.value ? parseDocument(props.entry.name, buffer.value).error : null))

function size(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} kB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function number(text) {
  const parsed = Number(text)
  return text === '' || !Number.isFinite(parsed) ? null : parsed
}

function json(entry) {
  return entry === null || entry === undefined ? '' : JSON.stringify(entry, null, 2)
}

function fieldsOf(item) {
  return entryFields(props.entry.name, item.value)
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const document = await desktop.readConfigFile(props.entry.name)
    const parsed = parseDocument(props.entry.name, document.text)
    if (parsed.error) {
      // A file the editor cannot structure is still editable as text.
      error.value = `${parsed.error} Edit it as JSON to repair it.`
      raw.value = true
      value.value = null
      buffer.value = document.text
      original.value = document.text
      return
    }
    value.value = parsed.value
    original.value = formatDocument(parsed.value)
    buffer.value = original.value
    jsonErrors.value = {}
  } catch (problem) {
    error.value = problem?.message || String(problem)
  } finally {
    loading.value = false
  }
}

function toggleOpen() {
  open.value = !open.value
  if (open.value && value.value === null && !error.value) load()
}

function toggleRaw() {
  if (raw.value) {
    const parsed = parseDocument(props.entry.name, buffer.value)
    if (parsed.error) return
    value.value = parsed.value
  } else {
    buffer.value = current.value
  }
  raw.value = !raw.value
}

function set(key, name, fieldValue) {
  value.value = updateEntry(props.entry.name, value.value, key, name, fieldValue)
}

function setJson(key, name, text) {
  const marker = `${key}:${name}`
  if (!text.trim()) {
    jsonErrors.value = { ...jsonErrors.value, [marker]: undefined }
    set(key, name, null)
    return
  }
  try {
    const parsed = JSON.parse(text)
    jsonErrors.value = { ...jsonErrors.value, [marker]: undefined }
    set(key, name, parsed)
  } catch (problem) {
    jsonErrors.value = { ...jsonErrors.value, [marker]: problem.message }
  }
}

function rename(key, name) {
  const renamed = renameEntry(props.entry.name, value.value, key, name)
  if (renamed === value.value) return
  value.value = renamed
  expanded.value = name.trim()
}

function remove(key) {
  value.value = removeEntry(props.entry.name, value.value, key)
  if (expanded.value === key) expanded.value = null
}

function add() {
  const added = addEntry(props.entry.name, value.value)
  value.value = added.value
  expanded.value = added.key
}

async function save() {
  saving.value = true
  error.value = null
  try {
    const text = raw.value ? buffer.value : current.value
    const document = await desktop.writeConfigFile(props.entry.name, text)
    // Compare what the file now holds the way the editor renders it, or the
    // trailing newline alone would leave the buffer looking modified.
    const parsed = parseDocument(props.entry.name, document.text)
    if (!parsed.error) value.value = parsed.value
    original.value = parsed.error ? document.text : formatDocument(parsed.value)
    buffer.value = original.value
    emit('saved', props.entry.name)
  } catch (problem) {
    error.value = problem?.message || String(problem)
  } finally {
    saving.value = false
  }
}

// A file deleted from the list outside the editor must not keep its contents.
watch(() => props.entry.exists, exists => {
  if (!exists && open.value) load()
})
</script>
