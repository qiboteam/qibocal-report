import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { state, apiFetch, resolveAuthor } from '../store.js'

/**
 * Composable providing statistics calculations, filtering, and data fetching.
 */
export function useStatisticsData() {
  const router = useRouter()

  const stats = ref(null)
  const loading = ref(true)
  const connectionError = ref(null)
  const protocolSearch = ref('')

  const activeServer = computed(() => state.activeServer)

  const totalReportsCount = computed(() => {
    if (stats.value?.total_reports !== undefined && stats.value?.total_reports > 0) {
      return stats.value.total_reports
    }
    if (stats.value?.platforms?.length) {
      return stats.value.platforms.reduce((sum, p) => sum + p.count, 0)
    }
    return 0
  })

  const platformsList = computed(() => stats.value?.platforms || [])
  const protocolsList = computed(() => stats.value?.protocols || [])

  const filteredProtocols = computed(() => {
    const all = protocolsList.value
    if (!protocolSearch.value.trim()) return all
    const q = protocolSearch.value.trim().toLowerCase()
    return all.filter(p => p.name.toLowerCase().includes(q))
  })

  const maxProtocolCount = computed(() => {
    const all = protocolsList.value
    return all.length ? Math.max(...all.map(p => p.count), 1) : 1
  })

  const authorsList = computed(() => {
    let list = []
    if (stats.value?.author_frequencies?.length) {
      list = stats.value.author_frequencies
    } else if (stats.value?.authors?.length) {
      list = stats.value.authors.map(a => ({
        name: a,
        count: (stats.value.author_counts && stats.value.author_counts[a]) || 1
      }))
    }
    if (!list.length) return []
    const map = new Map()
    for (const item of list) {
      const canonical = resolveAuthor(item.name, state.activeServer)
      map.set(canonical, (map.get(canonical) || 0) + item.count)
    }
    return Array.from(map.entries())
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
  })

  const tagsList = computed(() => {
    if (stats.value?.tag_frequencies?.length) {
      return stats.value.tag_frequencies
    }
    if (stats.value?.labels?.length) {
      return stats.value.labels.map(l => ({
        name: l,
        count: (stats.value.tag_counts && stats.value.tag_counts[l]) || 1
      }))
    }
    return []
  })

  const dateBins = computed(() => stats.value?.date_histogram || [])

  const maxDateCount = computed(() => {
    const bins = dateBins.value
    return bins.length ? Math.max(...bins.map(b => b.count), 1) : 1
  })

  function getPercentage(count, total) {
    if (!total || total === 0) return 0
    return Math.min(100, Math.max(0, Math.round((count / total) * 100)))
  }

  function filterBy(key, value) {
    if (!value && key !== 'clearRange') return
    if (key === 'dateRange' && typeof value === 'object') {
      state.pendingFilter = {
        key: 'dateRange',
        startDate: value.startDate,
        endDate: value.endDate
      }
    } else if (key === 'clearRange') {
      state.pendingFilter = { key: 'clearRange' }
    } else {
      state.pendingFilter = { key, value }
    }
    router.push('/dashboard')
  }

  async function loadStats() {
    loading.value = true
    connectionError.value = null
    try {
      const res = await apiFetch('/api/reports/stats')
      if (res.ok) {
        stats.value = await res.json()
      } else {
        connectionError.value = `Server responded with status ${res.status}`
      }
    } catch (err) {
      connectionError.value = `Could not connect to server: ${err.message}`
    } finally {
      loading.value = false
    }
  }

  return {
    stats,
    loading,
    connectionError,
    protocolSearch,
    activeServer,
    totalReportsCount,
    platformsList,
    protocolsList,
    filteredProtocols,
    maxProtocolCount,
    authorsList,
    tagsList,
    dateBins,
    maxDateCount,
    getPercentage,
    filterBy,
    loadStats
  }
}
