import { ref, watch, onUnmounted } from 'vue'
import { state, canManageQibocal } from '../store.js'
import { apiGetQibocal, apiGetQibocalOptions, apiInstallQibocal } from '../api.js'
import { readInstallationStream } from '../utils/installationStream.js'

async function readResponse(response) {
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || `Qibocal request failed (${response.status})`)
  return data
}

export function useQibocalEnvironment(onInstalled) {
  const loading = ref(false)
  const installing = ref(false)
  const environment = ref(null)
  const options = ref([])
  const selected = ref('')
  const error = ref('')
  const pypiError = ref('')
  const statusError = ref('')
  const installOutput = ref('')
  const success = ref('')
  let requestVersion = 0
  let disposed = false

  function isCurrent(version, server) {
    return !disposed && version === requestVersion && server === state.activeServer && canManageQibocal.value
  }

  async function refreshStatus() {
    const version = requestVersion
    const server = state.activeServer
    try {
      const data = await readResponse(await apiGetQibocal(server))
      if (isCurrent(version, server)) environment.value = data
    } catch (err) {
      if (isCurrent(version, server)) statusError.value = err.message
    }
  }

  async function refreshOptions() {
    if (!canManageQibocal.value || installing.value) return
    const version = ++requestVersion
    const server = state.activeServer
    loading.value = true
    error.value = ''
    success.value = ''
    pypiError.value = ''
    options.value = []
    selected.value = ''
    try {
      const data = await readResponse(await apiGetQibocalOptions(server))
      if (!isCurrent(version, server)) return
      environment.value = data
      statusError.value = ''
      options.value = data.options
      selected.value = data.options[0]?.id || ''
      pypiError.value = data.pypi_error || ''
    } catch (err) {
      if (isCurrent(version, server)) error.value = err.message
    } finally {
      if (isCurrent(version, server)) loading.value = false
    }
  }

  async function install() {
    if (!canManageQibocal.value || loading.value || installing.value || !options.value.some(option => option.id === selected.value)) return
    const version = requestVersion
    const server = state.activeServer
    installing.value = true
    error.value = ''
    success.value = ''
    installOutput.value = ''
    try {
      const data = await readInstallationStream(await apiInstallQibocal(selected.value, server), text => {
        if (isCurrent(version, server)) installOutput.value = (installOutput.value + text).slice(-300_000)
      })
      if (!isCurrent(version, server)) return
      environment.value = data
      success.value = `Qibocal ${data.version} installed successfully.`
      if (onInstalled) await onInstalled(data)
    } catch (err) {
      if (isCurrent(version, server)) error.value = err.message
    } finally {
      if (isCurrent(version, server)) installing.value = false
    }
  }

  watch(
    [
      () => state.activeServer?.id,
      () => state.activeServer?.url,
      () => state.auth.token,
      () => state.auth.user?.id,
      () => state.auth.user?.role,
      canManageQibocal
    ],
    () => {
      requestVersion++
      loading.value = false
      installing.value = false
      environment.value = null
      error.value = ''
      statusError.value = ''
      options.value = []
      selected.value = ''
      pypiError.value = ''
      installOutput.value = ''
      success.value = ''
      if (canManageQibocal.value) refreshStatus()
    },
    { immediate: true, flush: 'sync' }
  )

  onUnmounted(() => {
    disposed = true
    requestVersion++
  })

  return { loading, installing, environment, options, selected, error, pypiError, statusError, installOutput, success, refreshOptions, install }
}
