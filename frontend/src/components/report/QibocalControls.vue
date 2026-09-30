<template>
  <div v-if="canManageQibocal" class="no-print">
    <button
      type="button"
      :disabled="busy || installing"
      @click="open"
      class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-white border border-purple-200 text-purple-800 hover:bg-purple-50 transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
      :title="statusError || (environment?.version ? `Server Qibocal version: ${environment.version}` : 'Manage Qibocal in the server Python environment')"
    >
      {{ installing ? 'Installing Qibocal...' : missing || environment?.installed === false ? 'Install Qibocal' : 'Switch Qibocal Version' }}
    </button>

    <teleport to="body">
      <div
        v-if="show"
        role="dialog"
        aria-modal="true"
        aria-label="Install or switch Qibocal"
        class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs"
        @click.self="close"
        @keydown.esc="close"
      >
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-base font-bold text-gray-900">Install or switch Qibocal</h2>
            <button type="button" :disabled="installing" @click="close" aria-label="Close Qibocal installer" class="text-gray-400 hover:text-gray-700 cursor-pointer disabled:opacity-40">&times;</button>
          </div>
          <p class="text-xs text-gray-600 mt-3">
            Server: <strong>{{ state.activeServer?.name || state.activeServer?.url || 'Local Instance' }}</strong>
          </p>
          <p v-if="environment" class="text-xs text-gray-600 mt-1">
            Current version: <strong>{{ environment.installed ? environment.version : 'Not installed' }}</strong>
            <span v-if="environment.source === 'git'"> (Git)</span>
          </p>
          <p class="text-xs text-gray-500 mt-3 leading-relaxed">
            This changes Qibocal and its dependencies in the server's Python environment for all users.
            After installation, this report's cached plots will be regenerated with the selected version.
            Other cached reports are unchanged.
          </p>

          <loading-spinner v-if="loading" label="Fetching recent Qibocal versions..." class="my-6" />
          <template v-else>
            <p v-if="pypiError" role="alert" class="mt-4 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
              {{ pypiError }} You can still install from Git, or retry loading versions.
            </p>
            <fieldset :disabled="installing" class="mt-4 space-y-2">
              <legend class="text-xs font-semibold text-gray-700 mb-2">Installation source</legend>
              <label v-for="option in options" :key="option.id" class="flex items-center gap-2 p-3 rounded-xl border border-gray-200 text-xs text-gray-800 cursor-pointer hover:border-purple-300">
                <input v-model="selected" type="radio" :value="option.id" name="qibocal-version" class="accent-[#833dff]" />
                <span>{{ option.label }}</span>
              </label>
            </fieldset>
            <p v-if="selected === 'git'" class="text-[11px] text-gray-500 mt-2 break-all">
              Latest default branch of https://github.com/qiboteam/qibocal
            </p>
          </template>

          <p v-if="error" role="alert" class="mt-4 p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 whitespace-pre-wrap break-words">{{ error }}</p>
          <p v-if="installing" role="status" class="mt-4 text-xs text-purple-800">
            Installing in the server environment. This may take several minutes; keep this dialog open.
          </p>
          <div class="flex items-center justify-end gap-2 mt-5 pt-4 border-t border-gray-100">
            <button v-if="!installing && !loading" type="button" @click="open" class="px-3 py-1.5 text-xs font-semibold text-purple-700 cursor-pointer">Reload versions</button>
            <button type="button" :disabled="installing" @click="close" class="px-3 py-1.5 text-xs text-gray-600 cursor-pointer disabled:opacity-40">Cancel</button>
            <button type="button" :disabled="installing || loading || !selected" @click="install" class="px-4 py-1.5 rounded-xl text-xs font-semibold bm-btn-primary cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
              {{ installing ? 'Installing...' : 'Install and Regenerate' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { state, canManageQibocal } from '../../store.js'
import { useQibocalEnvironment } from '../../composables/useQibocalEnvironment.js'
import LoadingSpinner from '../LoadingSpinner.vue'

defineProps({
  missing: { type: Boolean, default: false },
  busy: { type: Boolean, default: false }
})
const emit = defineEmits(['installed', 'installing'])
const { show, loading, installing, environment, options, selected, error, pypiError, statusError, open, close, install } =
  useQibocalEnvironment(data => emit('installed', data))

watch(installing, value => emit('installing', value), { flush: 'sync' })
</script>
