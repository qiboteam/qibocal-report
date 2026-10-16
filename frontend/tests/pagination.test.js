import assert from 'node:assert/strict'
import { test } from 'node:test'

import { PAGE_CACHE_TTL_MS, usePagination } from '../src/composables/usePagination.js'

test('a page is kept for a while, across instances, and forgotten after', () => {
  const first = usePagination(10, 1)
  const key = first.getCacheKey('server|filters', 1)
  const realNow = Date.now
  let now = 1_000_000
  Date.now = () => now
  try {
    first.setCache(key, { items: [{ id: 'a' }], total: 1, total_pages: 1, page: 1 })
    // Another instance — the page mounted again after a round trip — sees it.
    const second = usePagination(10, 1)
    assert.equal(second.hasInCache(key), true)
    assert.deepEqual(second.getFromCache(key).items, [{ id: 'a' }])
    now += PAGE_CACHE_TTL_MS + 1
    assert.equal(second.hasInCache(key), false, 'past its lifetime, it is gone')
    assert.equal(second.getFromCache(key), undefined)
  } finally {
    Date.now = realNow
    first.clearCache()
  }
})
