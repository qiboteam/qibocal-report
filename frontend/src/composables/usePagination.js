import { ref, computed } from 'vue'

/**
 * Composable for paginated data management with pre-fetch memory caching.
 */
export function usePagination(initialPageSize = 10) {
  const currentPage = ref(1)
  const pageSize = ref(initialPageSize)
  const totalReports = ref(0)
  const totalPages = ref(1)
  const pageCache = new Map()

  const paginationRange = computed(() => {
    if (totalReports.value === 0) return { start: 0, end: 0 }
    const start = (currentPage.value - 1) * pageSize.value + 1
    const end = Math.min(start + pageSize.value - 1, totalReports.value)
    return { start, end }
  })

  const visiblePages = computed(() => {
    const total = totalPages.value
    const current = currentPage.value
    if (total <= 7) {
      return Array.from({ length: total }, (_, i) => i + 1)
    }

    const pages = []
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) pages.push(i)
      pages.push('...')
      pages.push(total)
    } else if (current >= total - 3) {
      pages.push(1)
      pages.push('...')
      for (let i = total - 4; i <= total; i++) pages.push(i)
    } else {
      pages.push(1)
      pages.push('...')
      pages.push(current - 1)
      pages.push(current)
      pages.push(current + 1)
      pages.push('...')
      pages.push(total)
    }
    return pages
  })

  function getAccessiblePages(current = currentPage.value, total = totalPages.value) {
    if (total <= 1) return []
    const accessible = new Set()
    if (current > 1) accessible.add(current - 1)
    if (current < total) accessible.add(current + 1)
    accessible.add(1)
    accessible.add(total)
    for (let p = Math.max(1, current - 2); p <= Math.min(total, current + 2); p++) {
      if (p >= 1 && p <= total) accessible.add(p)
    }
    accessible.delete(current)
    return Array.from(accessible).filter(p => p >= 1 && p <= total)
  }

  function getCacheKey(queryKey, page) {
    return `${queryKey}|p_${page}`
  }

  function clearCache() {
    pageCache.clear()
  }

  function getFromCache(cacheKey) {
    return pageCache.get(cacheKey)
  }

  function setCache(cacheKey, data) {
    pageCache.set(cacheKey, data)
  }

  function hasInCache(cacheKey) {
    return pageCache.has(cacheKey)
  }

  return {
    currentPage,
    pageSize,
    totalReports,
    totalPages,
    paginationRange,
    visiblePages,
    getAccessiblePages,
    getCacheKey,
    clearCache,
    getFromCache,
    setCache,
    hasInCache
  }
}
