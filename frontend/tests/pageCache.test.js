import assert from 'node:assert/strict'
import { test } from 'node:test'

import { PAGE_CACHE_TTL_MS, clearPages, hasPage, pageCacheKey, readPage, writePage } from '../src/utils/pageCache.js'

test('a page is kept for a while, and forgotten after', () => {
  const key = pageCacheKey('server|filters', 1)
  const now = 1_000_000
  writePage(key, { items: [{ id: 'a' }], total: 1 }, now)
  assert.equal(hasPage(key, now + 5_000), true)
  assert.deepEqual(readPage(key, now + 5_000).items, [{ id: 'a' }])
  assert.equal(hasPage(key, now + PAGE_CACHE_TTL_MS + 1), false, 'past its lifetime, it is gone')
  assert.equal(readPage(key, now + PAGE_CACHE_TTL_MS + 1), undefined)
  writePage(key, { items: [] }, now)
  clearPages()
  assert.equal(hasPage(key, now), false)
})
