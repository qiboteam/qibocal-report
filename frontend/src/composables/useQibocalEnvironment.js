import { ref, watch, onUnmounted } from 'vue'
import { state, canManageQibocal } from '../store.js'
import { apiGetQibocal, apiGetQibocalOptions, apiInstallQibocal } from '../api.js'

async function readResponse(response) {
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || `Qibocal request failed (${response.status})`)
  return data
}

export function useQibocalEnvironment(onInstalled) {
  const show = ref(false)
  const loading = ref(false)
  const installing = ref(false)
  const environment = ref(null)
  const options = ref([])
  const selected = ref('')
  const error = ref('')
  const pypiError = ref('')
  const statusError = ref('')
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

  async function open() {
    if (!canManageQibocal.value || installing.value) return
    const version = ++requestVersion
    const server = state.activeServer
    show.value = true
    loading.value = true
    error.value = ''
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

  function close() {
    if (installing.value) return
    show.value = false
    loading.value = false
    requestVersion++
  }

  async function install() {
    if (!canManageQibocal.value || loading.value || installing.value || !options.value.some(option => option.id === selected.value)) return
    const version = requestVersion
    const server = state.activeServer
    installing.value = true
    error.value = ''
    try {
      const data = await readResponse(await apiInstallQibocal(selected.value, server))
      if (!isCurrent(version, server)) return
      environment.value = data
      show.value = false
      await onInstalled(data)
    } catch (err) {
      if (isCurrent(version, server)) error.value = err.message
    } finally {
      if (isCurrent(version, server)) installing.value = false
    }
  }

  watch(
    () => [state.activeServer?.id, state.activeServer?.url, canManageQibocal.value],
    () => {
      requestVersion++
      show.value = false
      loading.value = false
      installing.value = false
      environment.value = null
      error.value = ''
      statusError.value = ''
      if (canManageQibocal.value) refreshStatus()
    },
    { immediate: true }
  )

  onUnmounted(() => {
    disposed = true
    requestVersion++
  })

  return { show, loading, installing, environment, options, selected, error, pypiError, statusError, open, close, install }
}
