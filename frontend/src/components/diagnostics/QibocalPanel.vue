<template>
  <div class="qibocal-panel">
    <div class="qibocal-settings">
      <p class="mb-2 text-xs">
        Current version: <strong>{{ environment ? environment.installed ? environment.version : 'Not installed' : statusError ? 'Unavailable' : 'Loading...' }}</strong>
        <span v-if="environment?.source === 'git'">
          (Git: <a v-if="environment.git_branch" :href="installedBranchUrl" target="_blank" rel="noopener noreferrer" class="installed-branch">{{ environment.git_branch }}</a><span v-else>branch unknown</span>)
        </span>
      </p>
      <p v-if="loading" role="status" class="text-xs mb-3">Fetching recent Qibocal versions...</p>
      <p id="qibocal-source-label" class="source-heading">Installation source</p>
      <div role="radiogroup" aria-labelledby="qibocal-source-label" class="version-grid">
        <button
          v-for="(option, index) in pypiOptions"
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
            <img :src="pypiLogo" :alt="option.label" class="pypi-logo" />
          </span>
          <span>{{ option.version }}</span>
        </button>
        <div v-if="gitOption" class="git-source" :class="{ selected: selected === 'git' }">
          <button
            :ref="element => versionButtons[pypiOptions.length] = element"
            type="button"
            role="radio"
            :aria-checked="selected === 'git'"
            :aria-label="gitLabel"
            :title="gitLabel"
            :tabindex="selected === 'git' ? 0 : -1"
            :disabled="loading || installing"
            class="version-button git-button"
            @click="selected = 'git'"
            @keydown="selectSource($event, pypiOptions.length)"
          >
            <span class="source-icon"><GitBranch :size="12" aria-hidden="true" /></span>
            <span class="git-label">Git: {{ gitBranch || 'default branch' }}</span>
          </button>
          <div class="branch-picker" :class="{ disabled: loading || installing || !gitBranches.length }">
            <ChevronDown :size="12" aria-hidden="true" />
            <select
              v-model="gitBranch"
              aria-label="Qibocal Git branch"
              title="Choose an official Qibocal Git branch"
              :disabled="loading || installing || !gitBranches.length"
              @focus="selected = 'git'"
              @change="selected = 'git'"
            >
              <option v-for="branch in gitBranches" :key="branch" :value="branch">{{ branch }}</option>
            </select>
          </div>
        </div>
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
          <span>{{ installing ? 'Installing...' : 'Install' }}</span>
        </button>
        <button type="button" :disabled="loading || installing" aria-label="Reload versions" title="Reload versions" class="icon-button" @click="refreshOptions">
          <RefreshCw :size="20" :class="{ 'animate-spin': loading }" aria-hidden="true" />
          <span>Refresh</span>
        </button>
      </div>
      <p class="installation-note">
        Changes the server's Python environment for all users. The open report or preview is regenerated after installation; other cached reports are unchanged.
      </p>
      <p v-if="selected === 'git'" class="installation-note">Official Qibocal repository: {{ gitBranch || 'default branch' }} (https://github.com/qiboteam/qibocal)</p>
      <p v-if="pypiError" role="alert" class="text-xs text-amber-300 mt-3">{{ pypiError }} Git remains available.</p>
      <p v-if="githubError" role="alert" class="text-xs text-amber-300 mt-3">{{ githubError }} The default Git branch remains available.</p>
      <p v-if="error || statusError" role="alert" class="text-xs text-red-300 mt-3 whitespace-pre-wrap">{{ error || statusError }}</p>
      <p v-if="success" role="status" class="text-xs text-green-300 mt-3">{{ success }}</p>
    </div>
    <div class="installation-output">
      <ansi-output :text="installOutput" :active="diagnostics.expanded && diagnostics.tab === 'qibocal'" label="Qibocal installation output" placeholder="Installer progress will appear here when you install or switch versions.">
        <template #heading>
          <p class="output-heading" role="status">{{ installing ? 'Installing Qibocal - live installer output' : 'Installer output' }}</p>
        </template>
        <template #actions>
          <button v-if="installing" type="button" :disabled="stopping" class="stop-button" aria-label="Stop Qibocal installation" :title="stopping ? 'Stopping installation...' : 'Stop Qibocal installation'" @click="stopInstallation">
            <X :size="12" aria-hidden="true" />
          </button>
        </template>
      </ansi-output>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { ChevronDown, GitBranch, Loader2, PackagePlus, RefreshCw, X } from 'lucide-vue-next'
import { state, canManageQibocal } from '../../store.js'
import { diagnostics } from '../../composables/useDiagnostics.js'
import { useQibocalEnvironment } from '../../composables/useQibocalEnvironment.js'
import AnsiOutput from './AnsiOutput.vue'
import pypiLogo from '../../assets/pypi.svg'

const versionButtons = ref([])

const { loading, installing, stopping, environment, options, selected, gitBranches, gitBranch, githubError, error, pypiError, statusError, installOutput, success, refreshOptions, install, stopInstallation } =
  useQibocalEnvironment(() => { diagnostics.qibocalRevision++ })
const pypiOptions = computed(() => options.value.filter(option => option.source === 'pypi'))
const gitOption = computed(() => options.value.find(option => option.source === 'git'))
const gitLabel = computed(() => `${gitOption.value?.label || 'Official Qibocal Git repository'}: ${gitBranch.value || 'default branch'}`)
const installedBranchUrl = computed(() => `https://github.com/qiboteam/qibocal/tree/${encodeURIComponent(environment.value?.git_branch || '')}`)

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
.installed-branch { color: #c8a8ff; text-decoration: underline; overflow-wrap: anywhere; }
.installed-branch:hover { color: #e1d0ff; }
.source-heading { margin: 0 0 8px; font-size: 11px; font-weight: 600; }
.version-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }
.version-button { display: flex; align-items: center; justify-content: center; gap: 6px; min-height: 30px; padding: 5px 8px; border: 1px solid #555; border-radius: 6px; background: #292929; color: #ddd; font-size: 11px; cursor: pointer; }
.version-button:hover:not(:disabled) { border-color: #a878ff; }
.version-button.selected { border-color: #a878ff; background: #53367b; color: #fff; }
.git-source { grid-column: 1 / -1; display: flex; align-items: stretch; min-width: 0; border: 1px solid #555; border-radius: 6px; background: #292929; }
.git-source.selected { border-color: #a878ff; background: #53367b; }
.git-button { flex: 1; min-width: 0; justify-content: flex-start; border: 0; background: transparent; }
.git-source.selected .git-button { color: #fff; }
.git-button svg, .branch-picker svg { width: 12px; height: 12px; flex-shrink: 0; }
.git-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.branch-picker { position: relative; display: flex; align-items: center; justify-content: center; width: 32px; flex-shrink: 0; border-left: 1px solid #555; }
.branch-picker.disabled { opacity: 0.5; }
.branch-picker select { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
.branch-picker select:disabled { cursor: not-allowed; }
.branch-picker:focus-within { outline: 2px solid #a878ff; outline-offset: -2px; border-radius: 0 5px 5px 0; }
.source-icon { display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; flex-shrink: 0; }
.pypi-logo { width: 20px; height: 20px; object-fit: contain; }
.installation-actions { display: flex; align-items: center; gap: 8px; margin-top: 18px; padding-top: 12px; border-top: 1px solid #444; }
.icon-button { display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-width: 40px; height: 40px; padding: 8px 12px; border: 1px solid #555; border-radius: 6px; color: #c8a8ff; font-size: 11px; cursor: pointer; }
.icon-button svg { width: 20px; height: 20px; flex-shrink: 0; }
.icon-button:hover:not(:disabled) { background: #343434; }
.install-button { background: #833dff; border-color: #833dff; color: #fff; }
.install-button:hover:not(:disabled) { background: #9457ff; }
.version-button:disabled, .icon-button:disabled { opacity: 0.5; cursor: not-allowed; }
.installation-note { margin: 8px 0 0; color: #999; font-size: 10px; line-height: 1.5; overflow-wrap: anywhere; }
.installation-output { display: flex; flex: 1; min-width: 0; min-height: 0; flex-direction: column; border-left: 1px solid #444; }
.output-heading { margin: 0; font-size: 12px; color: #ccc; }
.stop-button { display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; padding: 0; border: 1px solid #ef6666; border-radius: 3px; background: #722c2c; color: #ffb3b3; cursor: pointer; }
.stop-button:hover:not(:disabled) { background: #963636; }
.stop-button:disabled { opacity: 0.5; cursor: not-allowed; }
@media (max-width: 640px) {
  .qibocal-panel { flex-direction: column; }
  .qibocal-settings { width: 100%; max-height: 45%; }
  .installation-output { flex: 1; border-left: 0; border-top: 1px solid #444; min-height: 100px; }
}
</style>
