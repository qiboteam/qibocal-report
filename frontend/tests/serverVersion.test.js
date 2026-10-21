import assert from 'node:assert/strict'
import { test } from 'node:test'

import { API_VERSION, serverCompatibility } from '../src/utils/serverVersion.js'

test('a server is read against the API version of this dashboard', () => {
  const same = serverCompatibility({ version: '0.1.0a1', api_version: API_VERSION, commit: '0123456789abcdef' })
  assert.equal(same.state, 'ok')
  assert.equal(same.label, 'v0.1.0a1')
  assert.match(same.title, /commit 0123456/)
  assert.equal(serverCompatibility({ version: '9.0.0', api_version: API_VERSION + 1 }).state, 'newer')
  assert.match(serverCompatibility({ version: '0.0.1', api_version: API_VERSION - 1 }).title, /update the server/)
  assert.equal(serverCompatibility(null).state, 'unknown', 'no answer: older than the first release')
})
