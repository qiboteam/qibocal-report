import assert from 'node:assert/strict'
import { test } from 'node:test'

import { uploadDestinations, uploadFailure, uploadState } from '../src/utils/uploads.js'

test('a report goes to any registered server but its own', () => {
  const servers = [{ id: 'a', url: 'http://a.example/' }, { id: 'b', url: 'http://b.example' }, { id: 'c' }]
  assert.deepEqual(uploadDestinations(servers, { url: 'http://a.example' }).map(server => server.id), ['b'])
  assert.deepEqual(uploadDestinations(servers, null).map(server => server.id), ['a', 'b'])
})

test('a destination is ready, wants a sign-in, or refuses', () => {
  assert.equal(uploadState({ accepted: true, auth_enabled: false }).state, 'ready')
  assert.equal(uploadState({ accepted: true, auth_enabled: true }).state, 'ready')
  assert.equal(uploadState({ accepted: false, auth_enabled: true }, { registered: false }).state, 'sign-in')
  assert.match(uploadState({ accepted: false, auth_enabled: true }, { registered: false }).text, /register it/)
  assert.equal(uploadState({ accepted: false, auth_enabled: true }, { registered: true, signedIn: false }).state, 'sign-in')
  assert.equal(uploadState({ accepted: false, auth_enabled: true }, { registered: true, signedIn: true }).state, 'refused')
  assert.equal(uploadState(null).state, 'unreachable')
})

test('a failed upload says why', () => {
  assert.equal(uploadFailure(409, 'A report named run is already on this server.'), 'A report named run is already on this server.')
  assert.equal(uploadFailure(403), 'Your account may not upload there.')
  assert.equal(uploadFailure(500), 'The server answered 500.')
})
