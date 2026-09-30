<template>
  <div class="qibocal-panel">
    <div class="qibocal-settings">
      <p class="mb-2 text-xs">
        Current version: <strong>{{ environment ? environment.installed ? environment.version : 'Not installed' : statusError ? 'Unavailable' : 'Loading...' }}</strong>
        <span v-if="environment?.source === 'git'"> (Git)</span>
      </p>
      <p v-if="loading" role="status" class="text-xs mb-3">Fetching recent Qibocal versions...</p>
      <p id="qibocal-source-label" class="source-heading">Installation source</p>
      <div role="radiogroup" aria-labelledby="qibocal-source-label" class="version-grid">
        <button
          v-for="(option, index) in options"
          :key="option.id"
          :ref="element => versionButtons[index] = element"
          type="button"
          role="radio"
          :aria-checked="selected === option.id"
          :aria-label="option.label"
          :title="option.label"
          :tabindex="selected === option.id ? 0 : -1"
          :disabled="loading || installing"
          class="version-button"
          :class="{ selected: selected === option.id }"
          @click="selected = option.id"
          @keydown="selectSource($event, index)"
        >
          <span class="source-icon">
            <img v-if="option.source === 'pypi'" :src="pypiLogo" :alt="option.label" class="pypi-logo" />
            <GitBranch v-else :size="12" aria-hidden="true" />
          </span>
          <span>{{ option.source === 'pypi' ? option.version : 'Latest Git' }}</span>
        </button>
      </div>
      <div class="installation-actions">
        <button
          type="button"
          :disabled="installing || loading || !selected"
          :aria-label="installing ? 'Installing Qibocal...' : 'Install / Switch version'"
          :title="installing ? 'Installing Qibocal...' : 'Install / Switch version'"
          class="icon-button install-button"
          @click="install"
        >
          <Loader2 v-if="installing" :size="20" class="animate-spin" aria-hidden="true" />
          <PackagePlus v-else :size="20" aria-hidden="true" />
        </button>
        <button type="button" :disabled="loading || installing" aria-label="Reload versions" title="Reload versions" class="icon-button" @click="refreshOptions">
          <RefreshCw :size="20" :class="{ 'animate-spin': loading }" aria-hidden="true" />
        </button>
      </div>
      <p class="installation-note">
        Changes the server's Python environment for all users. The open report or preview is regenerated after installation; other cached reports are unchanged.
      </p>
      <p v-if="selected === 'git'" class="installation-note">Latest default branch of https://github.com/qiboteam/qibocal</p>
      <p v-if="pypiError" role="alert" class="text-xs text-amber-300 mt-3">{{ pypiError }} Git remains available.</p>
      <p v-if="error || statusError" role="alert" class="text-xs text-red-300 mt-3 whitespace-pre-wrap">{{ error || statusError }}</p>
      <p v-if="success" role="status" class="text-xs text-green-300 mt-3">{{ success }}</p>
    </div>
    <div class="installation-output">
      <p class="output-heading" role="status">{{ installing ? 'Installing Qibocal - live installer output' : 'Installer output' }}</p>
      <ansi-output :text="installOutput" :active="diagnostics.expanded && diagnostics.tab === 'qibocal'" label="Qibocal installation output" placeholder="Installer progress will appear here when you install or switch versions." />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { GitBranch, Loader2, PackagePlus, RefreshCw } from 'lucide-vue-next'
import { state, canManageQibocal } from '../../store.js'
import { diagnostics } from '../../composables/useDiagnostics.js'
import { useQibocalEnvironment } from '../../composables/useQibocalEnvironment.js'
import AnsiOutput from './AnsiOutput.vue'
import pypiLogo from '../../assets/pypi.svg'

const versionButtons = ref([])

const { loading, installing, environment, options, selected, error, pypiError, statusError, installOutput, success, refreshOptions, install } =
  useQibocalEnvironment(() => { diagnostics.qibocalRevision++ })

async function selectSource(event, index) {
  if (loading.value || installing.value || !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  const next = event.key === 'Home' ? 0 : event.key === 'End' ? options.value.length - 1 : (index + (['ArrowRight', 'ArrowDown'].includes(event.key) ? 1 : -1) + options.value.length) % options.value.length
  selected.value = options.value[next].id
  await nextTick()
  versionButtons.value[next]?.focus()
}

watch(installing, value => { diagnostics.installing = value }, { flush: 'sync' })
watch(
  () => [diagnostics.expanded, diagnostics.tab, state.activeServer?.id, state.activeServer?.url, canManageQibocal.value],
  () => {
    if (diagnostics.expanded && diagnostics.tab === 'qibocal' && !options.value.length && !loading.value && !installing.value) refreshOptions()
  },
  { immediate: true }
)
</script>

<style scoped>
.qibocal-panel { display: flex; flex: 1; min-height: 0; overflow: auto; }
.qibocal-settings { width: 340px; flex-shrink: 0; padding: 16px; overflow-y: auto; }
.source-heading { margin: 0 0 8px; font-size: 11px; font-weight: 600; }
.version-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }
.version-button { display: flex; align-items: center; justify-content: center; gap: 6px; min-height: 30px; padding: 5px 8px; border: 1px solid #555; border-radius: 6px; background: #292929; color: #ddd; font-size: 11px; cursor: pointer; }
.version-button:hover:not(:disabled) { border-color: #a878ff; }
.version-button.selected { border-color: #a878ff; background: #53367b; color: #fff; }
.source-icon { display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; flex-shrink: 0; }
.pypi-logo { width: 20px; height: 20px; object-fit: contain; }
.installation-actions { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
.icon-button { display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; padding: 8px; border: 1px solid #555; border-radius: 6px; color: #c8a8ff; cursor: pointer; }
.icon-button svg { width: 20px; height: 20px; flex-shrink: 0; }
.icon-button:hover:not(:disabled) { background: #343434; }
.install-button { background: #833dff; border-color: #833dff; color: #fff; }
.install-button:hover:not(:disabled) { background: #9457ff; }
.version-button:disabled, .icon-button:disabled { opacity: 0.5; cursor: not-allowed; }
.installation-note { margin: 8px 0 0; color: #999; font-size: 10px; line-height: 1.5; overflow-wrap: anywhere; }
.installation-output { display: flex; flex: 1; min-width: 0; min-height: 0; flex-direction: column; border-left: 1px solid #444; }
.output-heading { margin: 0; padding: 10px 12px 0; font-size: 12px; color: #ccc; }
@media (max-width: 640px) {
  .qibocal-panel { flex-direction: column; }
  .qibocal-settings { width: 100%; max-height: 45%; }
  .installation-output { flex: 1; border-left: 0; border-top: 1px solid #444; min-height: 100px; }
}
</style>
