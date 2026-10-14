<template>
  <div class="max-w-5xl mx-auto px-5 py-8">
    <div class="mb-5">
      <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Notebooks</h1>
      <p class="mt-1 text-xs text-gray-500">
        Open a JupyterLab or Marimo session — here, over SSH, or through SLURM. Saved connections are
        the very ones <code class="lx-mono">qibocal notebook</code> uses.
      </p>
    </div>

    <div class="grid gap-4 lg:grid-cols-[16rem_1fr] items-start">
      <aside class="space-y-2">
        <button
          type="button"
          class="bm-card w-full text-left p-3 transition"
          :class="selected === null ? 'ring-2 ring-[#833dff]/30' : ''"
          @click="choose(null)"
        >
          <span class="text-xs font-medium text-gray-900">New session</span>
          <span class="block lx-help !mt-0.5">Start without saving anything.</span>
        </button>

        <button
          v-for="(options, name) in state.notebooks"
          :key="name"
          type="button"
          class="bm-card w-full text-left p-3 transition"
          :class="selected === name ? 'ring-2 ring-[#833dff]/30' : ''"
          @click="choose(name)"
        >
          <span class="text-xs font-medium text-gray-900 truncate block">{{ name }}</span>
          <span class="block lx-help !mt-0.5 truncate">{{ describeConnection(options) }}</span>
        </button>
      </aside>

      <section class="bm-card p-5">
        <div class="flex flex-wrap items-center gap-2 mb-4">
          <h2 class="text-sm font-semibold text-gray-900">
            {{ selected || 'New session' }}
          </h2>
          <button
            v-if="selected"
            type="button"
            class="lx-action ml-auto"
            @click="remove(selected)"
          >
            <Trash2 class="w-3.5 h-3.5" /> Remove
          </button>
        </div>

        <!-- Nothing is required: empty, the session is a local one. -->
        <div class="grid gap-4 sm:grid-cols-2">
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
            <input
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
              :label="field.label"
              :help="field.help"
              :info="field.info"
              :error="errors[field.name]"
              :warning="warnings[field.name]"
            >
              <div v-if="field.type === 'number'" class="flex items-center gap-2">
                <input :id="id" v-model="values[field.name]" type="number" min="1" class="lx-input lx-mono" />
                <span class="text-[11px] text-gray-400 shrink-0">{{ field.unit }}</span>
              </div>
              <path-picker
                v-else-if="field.name === 'workdir' && !values.ssh"
                :id="id"
                v-model="values[field.name]"
                title="Choose the working directory"
              />
              <input
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

        <div class="flex flex-wrap items-center gap-2.5 mt-5">
          <button
            type="button"
            class="lx-primary"
            :disabled="!valid || starting"
            @click="start"
          >
            {{ starting ? 'Opening…' : 'Open session' }}
          </button>

          <div class="flex items-center gap-2">
            <input
              v-model.trim="saveName"
              type="text"
              class="lx-input w-40"
              placeholder="Connection name"
              aria-label="Connection name"
            />
            <button type="button" class="lx-action" :disabled="!saveName || !valid" @click="save">
              <Bookmark class="w-3.5 h-3.5" /> Save
            </button>
          </div>

          <code class="lx-mono text-gray-400 truncate">{{ preview }}</code>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Bookmark, ChevronRight, Trash2 } from 'lucide-vue-next'
import FormField from '../components/FormField.vue'
import PathPicker from '../components/PathPicker.vue'
import SegmentedControl from '../components/SegmentedControl.vue'
import { desktop } from '../bridge.js'
import { state, attempt, fail, notify, refreshNotebooks } from '../state.js'
import {
  NOTEBOOK_FIELDS,
  defaultNotebookOptions,
  describeConnection,
  normalizeNotebookOptions,
  toEditorValues
} from '../lib/notebooks.js'

const router = useRouter()

const primaryFields = NOTEBOOK_FIELDS.filter(field => !field.advanced)
const advancedFields = NOTEBOOK_FIELDS.filter(field => field.advanced)

const selected = ref(null)
const saveName = ref('')
const starting = ref(false)
const values = reactive(defaultNotebookOptions())

const normalized = computed(() => normalizeNotebookOptions(values))
const errors = computed(() => normalized.value.errors)
const warnings = computed(() => normalized.value.warnings)
const valid = computed(() => normalized.value.valid)

const preview = computed(() => {
  const parts = ['qibocal', 'notebook', 'connect']
  if (selected.value) parts.push(selected.value)
  for (const [key, value] of Object.entries(normalized.value.options)) {
    if (key === 'marimo') parts.push(value ? '--marimo' : '--jupyter')
    else parts.push(`--${key}`, String(value))
  }
  return parts.join(' ')
})

function choose(name) {
  selected.value = name
  saveName.value = name || ''
  Object.assign(values, toEditorValues(name ? state.notebooks[name] : {}))
}

async function start() {
  starting.value = true
  try {
    await desktop.startNotebook({ connection: selected.value, ...normalized.value.options })
    notify('Opening the notebook session; its address appears in the output.')
    router.push({ name: 'processes' })
  } catch (error) {
    fail(error)
  } finally {
    starting.value = false
  }
}

async function save() {
  const saved = await attempt(
    () => desktop.saveNotebook(saveName.value, normalized.value.options),
    `Connection '${saveName.value}' saved.`
  )
  if (saved === undefined) return
  state.notebooks = saved
  selected.value = saveName.value
}

async function remove(name) {
  const left = await attempt(() => desktop.removeNotebook(name), `Connection '${name}' removed.`)
  if (left === undefined) return
  state.notebooks = left
  choose(null)
}

onMounted(() => refreshNotebooks())
// Picking a connection in the list replaces the editor contents.
watch(() => state.notebooks, () => {
  if (selected.value && !state.notebooks[selected.value]) choose(null)
})
</script>
