import assert from 'node:assert/strict'
import { test } from 'node:test'

import { isRecent, timeAgo } from '../src/lib/time.js'

const NOW = Date.UTC(2026, 9, 15, 12, 0, 0)

test('the distance from now is said in words, coarsely', () => {
  assert.equal(timeAgo(NOW, NOW), 'just now')
  assert.equal(timeAgo(NOW - 30_000, NOW), 'just now')
  assert.equal(timeAgo(NOW - 60_000, NOW), '1 minute ago')
  assert.equal(timeAgo(NOW - 5 * 60_000, NOW), '5 minutes ago')
  assert.equal(timeAgo(NOW - 3 * 3_600_000, NOW), '3 hours ago')
  assert.equal(timeAgo(NOW - 2 * 86_400_000, NOW), '2 days ago')
  assert.equal(timeAgo(NOW + 60_000, NOW), 'just now', 'a clock ahead of us is not in the future')
})

test('the bubble keeps a day', () => {
  assert.equal(isRecent(NOW - 23 * 3_600_000, NOW), true)
  assert.equal(isRecent(NOW - 25 * 3_600_000, NOW), false)
})
