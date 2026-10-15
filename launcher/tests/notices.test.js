import assert from 'node:assert/strict'
import { test } from 'node:test'

import { NOTICES_KEY, loadNotices, nextNoticeId, storeNotices } from '../src/lib/notices.js'

function memory() {
  const map = new Map()
  return { getItem: key => map.get(key) ?? null, setItem: (key, value) => map.set(key, value) }
}

test('notifications survive a round trip through the storage', () => {
  const storage = memory()
  const notices = [
    { id: 2, text: 'Second', kind: 'error', at: 20, link: { name: 'servers' }, archived: false },
    { id: 1, text: 'First', kind: 'info', at: 10, link: null, archived: true }
  ]
  storeNotices(storage, notices)
  assert.deepEqual(loadNotices(storage), notices)
  assert.equal(nextNoticeId(notices), 3)
})

test('nonsense in the storage is nothing, not a crash', () => {
  const storage = memory()
  storage.setItem(NOTICES_KEY, '{"not": "a list"}')
  assert.deepEqual(loadNotices(storage), [])
  storage.setItem(NOTICES_KEY, '[{"text": 1}, {"text": "ok", "at": 5, "kind": "odd"}]')
  assert.deepEqual(loadNotices(storage), [{ id: 0, text: 'ok', kind: 'info', at: 5, link: null, archived: false }])
  assert.deepEqual(loadNotices(null), [])
  assert.equal(nextNoticeId([]), 1)
})
