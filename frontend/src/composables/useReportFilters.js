import { reactive, computed } from 'vue'

/**
 * Composable to manage dashboard report filters and query key generation.
 */
export function useReportFilters() {
  const filters = reactive({
    q: '',
    author: '',
    date: '',
    protocols: [],
    labels: [],
    sort_by: 'date_desc'
  })

  const hasActiveFilters = computed(() => {
    return Boolean(
      filters.author ||
      filters.date ||
      filters.protocols.length > 0 ||
      filters.labels.length > 0
    )
  })

  function toggleProtocol(name) {
    const idx = filters.protocols.indexOf(name)
    if (idx >= 0) {
      filters.protocols.splice(idx, 1)
    } else {
      filters.protocols.push(name)
    }
  }

  function toggleLabel(name) {
    const idx = filters.labels.indexOf(name)
    if (idx >= 0) {
      filters.labels.splice(idx, 1)
    } else {
      filters.labels.push(name)
    }
  }

  function updateFilter({ key, value }) {
    if (key === 'author') filters.author = value
    if (key === 'date') filters.date = value
  }

  function resetFilters() {
    filters.q = ''
    filters.author = ''
    filters.date = ''
    filters.protocols = []
    filters.labels = []
  }

  function getFilterQueryKey(activeServer, pageSize) {
    const serverKey = activeServer?.id || activeServer?.url || 'local'
    const protos = [...filters.protocols].sort().join(',')
    const labels = [...filters.labels].sort().join(',')
    return `${serverKey}|${filters.q.trim().toLowerCase()}|${filters.author}|${filters.date}|${protos}|${labels}|${filters.sort_by}|${pageSize}`
  }

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
