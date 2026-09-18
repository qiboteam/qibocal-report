import { computed, watch } from 'vue'
import { state, persistSearchState, resetSearchState, hasActiveSearchFilters } from '../store.js'

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

  function updateFilter({ key, value }) {
    if (key === 'author') filters.author = value
    if (key === 'platform') filters.platform = value
    if (key === 'date') filters.date = value
    persistSearchState()
  }

  function resetFilters() {
    resetSearchState()
  }

  function getFilterQueryKey(activeServer, pageSize) {
    const serverKey = activeServer?.id || activeServer?.url || 'local'
    const protos = [...(filters.protocols || [])].sort().join(',')
    const labels = [...(filters.labels || [])].sort().join(',')
    const qStr = (filters.q || '').trim().toLowerCase()
    return `${serverKey}|${qStr}|${filters.author || ''}|${filters.platform || ''}|${filters.date || ''}|${protos}|${labels}|${filters.sort_by || 'date_desc'}|${pageSize}`
  }

  watch(
    () => [filters.q, filters.sort_by, filters.author, filters.platform, filters.date],
    () => {
      persistSearchState()
    }
  )

  return {
    filters,
    hasActiveFilters,
    toggleProtocol,
    toggleLabel,
    updateFilter,
    resetFilters,
    getFilterQueryKey
  }
}
