import { computed, watch } from 'vue'
import { state, persistSearchState, resetSearchState, hasActiveSearchFilters, resolveAuthor } from '../store.js'

/**
 * Composable to manage dashboard report filters and query key generation.
 */
export function useReportFilters() {
  const filters = state.searchState.filters

  const hasActiveFilters = computed(() => {
    return hasActiveSearchFilters(filters)
  })

  function toggleProtocol(name) {
    if (!Array.isArray(filters.protocols)) {
      filters.protocols = []
    }
    const idx = filters.protocols.indexOf(name)
    if (idx >= 0) {
      filters.protocols.splice(idx, 1)
    } else {
      filters.protocols.push(name)
    }
    persistSearchState()
  }

  function toggleLabel(name) {
    if (!Array.isArray(filters.labels)) {
      filters.labels = []
    }
    const idx = filters.labels.indexOf(name)
    if (idx >= 0) {
      filters.labels.splice(idx, 1)
    } else {
      filters.labels.push(name)
    }
    persistSearchState()
  }

  function togglePlatform(name) {
    if (!name) return
    if (filters.platform === name) {
      filters.platform = ''
    } else {
      filters.platform = name
    }
    persistSearchState()
  }

  function toggleAuthor(name) {
    if (!name) return
    const resolved = resolveAuthor(name, state.activeServer) || name
    if (filters.author === resolved || filters.author === name) {
      filters.author = ''
    } else {
      filters.author = resolved
    }
    persistSearchState()
  }

  function toggleQubit(qubit) {
    if (qubit === null || qubit === undefined) return
    if (!Array.isArray(filters.qubits)) {
      filters.qubits = []
    }
    const qStr = String(qubit).trim()
    const idx = filters.qubits.indexOf(qStr)
    if (idx >= 0) {
      filters.qubits.splice(idx, 1)
    } else {
      filters.qubits.push(qStr)
    }
    persistSearchState()
  }

  function updateFilter({ key, value, startDate, endDate }) {
    if (key === 'author') filters.author = value
    if (key === 'platform') filters.platform = value
    if (key === 'date') {
      filters.date = value || ''
      filters.startDate = value || ''
      filters.endDate = value || ''
    }
    if (key === 'dateRange') {
      const s = startDate !== undefined ? startDate : (value?.startDate ?? value?.start ?? '')
      const e = endDate !== undefined ? endDate : (value?.endDate ?? value?.end ?? '')
      filters.startDate = s || ''
      filters.endDate = e || ''
      filters.date = (s && e && s === e) ? s : ''
    }
    if (key === 'startDate') {
      filters.startDate = value || ''
      filters.date = (filters.startDate && filters.endDate && filters.startDate === filters.endDate) ? filters.startDate : ''
    }
    if (key === 'endDate') {
      filters.endDate = value || ''
      filters.date = (filters.startDate && filters.endDate && filters.startDate === filters.endDate) ? filters.startDate : ''
    }
    persistSearchState()
  }

  function resetFilters() {
    resetSearchState()
  }

  function getFilterQueryKey(activeServer, pageSize) {
    const serverKey = activeServer?.id || activeServer?.url || 'local'
    const protos = [...(filters.protocols || [])].sort().join(',')
    const labels = [...(filters.labels || [])].sort().join(',')
    const qubits = [...(filters.qubits || [])].sort().join(',')
    const qStr = (filters.q || '').trim().toLowerCase()
    const start = filters.startDate || filters.date || ''
    const end = filters.endDate || filters.date || ''
    return `${serverKey}|${qStr}|${filters.author || ''}|${filters.platform || ''}|${start}|${end}|${protos}|${labels}|${qubits}|${filters.sort_by || 'date_desc'}|${pageSize}`
  }

  watch(
    () => [filters.q, filters.sort_by, filters.author, filters.platform, filters.date, filters.startDate, filters.endDate, filters.qubits?.length],
    () => {
      persistSearchState()
    }
  )

  return {
    filters,
    hasActiveFilters,
    toggleProtocol,
    toggleLabel,
    togglePlatform,
    toggleAuthor,
    toggleQubit,
    updateFilter,
    resetFilters,
    getFilterQueryKey
  }
}
