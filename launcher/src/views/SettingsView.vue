<template>
  <div class="max-w-4xl mx-auto px-5 py-8 space-y-5">
    <div>
      <h1 class="text-xl font-semibold text-gray-900 tracking-tight">Configuration</h1>
      <p class="mt-1 text-xs text-gray-500">
        Which Qibocal installation the launcher drives, and the files it shares with the command line.
      </p>
    </div>

    <section class="bm-card p-5">
      <h2 class="text-sm font-semibold text-gray-900 mb-3">Qibocal installation</h2>

      <div v-if="environment?.executable" class="flex flex-wrap items-center gap-x-4 gap-y-1 mb-4 text-xs">
        <span class="inline-flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span class="font-medium text-gray-800">{{ environment.version || 'available' }}</span>
        </span>
        <code class="lx-mono text-gray-500 truncate">{{ environment.executable }}</code>
        <span class="text-[11px] text-gray-400">found through {{ environment.source }}</span>
      </div>
      <p v-else class="text-xs text-amber-700 bg-amber-50 rounded-xl px-3 py-2 mb-4">
        No <code class="lx-mono">qibocal</code> command line was found. Install it, or point the launcher at
        the environment holding it — a virtual environment folder works too.
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

      <details v-if="environment?.searched?.length" class="mt-4">
        <summary class="text-[11px] text-gray-400 cursor-pointer select-none">Where the launcher looked</summary>
        <ul class="mt-2 space-y-0.5">
          <li v-for="place in environment.searched" :key="place" class="lx-mono text-gray-400 truncate">{{ place }}</li>
        </ul>
      </details>
    </section>

    <section class="bm-card p-5">
      <div class="flex flex-wrap items-center gap-2 mb-3">
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

      <table class="w-full text-xs">
        <tbody>
          <tr v-for="entry in state.configEntries" :key="entry.name" class="border-t border-gray-100 first:border-0">
            <td class="py-2 pr-3">
              <label class="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  class="mt-0.5 accent-[#833dff]"
                  :disabled="!entry.exists"
                  :checked="chosen.includes(entry.name)"
                  @change="toggle(entry.name)"
                />
                <span>
                  <span class="block font-medium text-gray-900">{{ entry.name }}</span>
                  <span class="block lx-help !mt-0">{{ entry.description }}</span>
                </span>
              </label>
            </td>
            <td class="py-2 text-right text-gray-400 whitespace-nowrap">
              {{ entry.exists ? size(entry.size) : 'not created' }}
            </td>
          </tr>
        </tbody>
      </table>

      <div class="flex items-center gap-2 mt-4">
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
            <button type="button" class="text-[#833dff] hover:underline" @click="openExternal(WEB_FRONTEND)">
              {{ WEB_FRONTEND }}
            </button>
          </dd>
        </div>
      </dl>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { FolderOpen, RotateCcw, Terminal, Trash2 } from 'lucide-vue-next'
import { chooseDirectory, chooseFile, desktop, openExternal, revealInFileManager } from '../bridge.js'
import {
  state,
  attempt,
  refreshConfigEntries,
  refreshEnvironment,
  refreshNotebooks,
  refreshPreferences,
  refreshServers
} from '../state.js'

const WEB_FRONTEND = 'https://qibo.science/qibocal-report'

const chosen = ref([])
const platform = ref({ os: '—', arch: '' })

const environment = computed(() => state.environment)
const preferredExecutable = computed(() => state.preferences?.executable || null)

function size(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} kB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function toggle(name) {
  chosen.value = chosen.value.includes(name)
    ? chosen.value.filter(entry => entry !== name)
    : [...chosen.value, name]
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
  const updated = await attempt(() => desktop.setExecutable(null), 'Back to automatic detection.')
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
  await Promise.all([refreshConfigEntries(), refreshServers(), refreshNotebooks(), refreshPreferences()])
}

async function reveal(path) {
  await attempt(() => revealInFileManager(path))
}

onMounted(async () => {
  await Promise.all([refreshEnvironment(), refreshConfigEntries(), refreshPreferences()])
  platform.value = (await attempt(() => desktop.platform())) || platform.value
})
</script>
