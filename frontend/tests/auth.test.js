import assert from 'node:assert/strict'
import { beforeEach, afterEach, test, mock } from 'node:test'

const storage = new Map()
globalThis.localStorage = {
  getItem: key => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, String(value)),
  removeItem: key => storage.delete(key)
}
globalThis.sessionStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {}
}

const {
  state, setActiveServer, checkActiveServerAuth, setServerAuth,
  getActiveAuthToken, getActiveUser, getActiveServerUrl, loginActiveServer,
  logoutActiveServer, isAuthenticated, isViewer, canEdit, isAdmin
} = await import('../src/store.js')
const { apiFetch } = await import('../src/api.js')

const server = { id: 'first', name: 'First', url: 'http://first.example' }
const otherServer = { id: 'second', name: 'Second', url: 'http://second.example' }
const viewer = { id: 'viewer', username: 'viewer', role: 'viewer' }
const editor = { id: 'editor', username: 'editor', role: 'editor' }

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status })
}

beforeEach(() => {
  setActiveServer(null)
  setServerAuth(server, null, null)
  setServerAuth(otherServer, null, null)
  storage.clear()
  state.servers = [server, otherServer]
})

afterEach(() => mock.restoreAll())

test('a registered server can switch between open and authenticated modes', async () => {
  let enabled = false
  mock.method(globalThis, 'fetch', async (url, options) => {
    if (url.endsWith('/api/auth/status')) {
      assert.equal(options.cache, 'no-store')
      return json({ auth_enabled: enabled })
    }
    if (url.endsWith('/api/auth/login')) {
      return json({ access_token: 'viewer-session', user: viewer })
    }
    if (url.endsWith('/api/auth/me')) return json(viewer)
    assert.fail(`Unexpected request: ${url}`)
  })

  assert.equal(await setActiveServer(server), true)
  assert.equal(state.auth.enabled, false)
  assert.equal(isAuthenticated.value, true)
  assert.equal(canEdit.value, true)
  assert.equal(isAdmin.value, true)

  enabled = true
  assert.equal(await setActiveServer(server), true)
  assert.equal(state.auth.enabled, true)
  assert.equal(isAuthenticated.value, false)
  assert.equal(canEdit.value, false)
  assert.equal(isAdmin.value, false)

  await loginActiveServer('viewer', 'password')
  assert.equal(isViewer.value, true)
  assert.equal(isAuthenticated.value, true)
  assert.equal(canEdit.value, false)

  enabled = false
  assert.equal(await setActiveServer(server), true)
  assert.equal(getActiveAuthToken(server), null)
  assert.equal(canEdit.value, true)
  assert.equal(isAdmin.value, true)

  enabled = true
  assert.equal(await setActiveServer(server), true)
  assert.equal(isAuthenticated.value, false)
  assert.equal(state.activeServer.id, server.id)
})

test('sessions are isolated per server and logout allows a different account', async () => {
  mock.method(globalThis, 'fetch', async (url, options) => {
    if (url.endsWith('/api/auth/status')) return json({ auth_enabled: true })
    if (url.endsWith('/api/auth/me')) return json(viewer)
    if (url.endsWith('/api/auth/login')) {
      const { username } = JSON.parse(options.body)
      return json({ access_token: `${username}-session`, user: username === 'viewer' ? viewer : editor })
    }
    assert.fail(`Unexpected request: ${url}`)
  })

  await setActiveServer(server)
  await loginActiveServer('viewer', 'password')
  assert.equal(getActiveAuthToken(otherServer), null)
  assert.equal(getActiveUser(otherServer), null)
  assert.equal(getActiveServerUrl(otherServer), otherServer.url)

  setServerAuth(otherServer, 'other-session', editor)
  logoutActiveServer(otherServer)
  assert.equal(getActiveAuthToken(otherServer), null)
  assert.equal(state.auth.user.role, 'viewer')
  setServerAuth(otherServer, 'other-session', editor)

  logoutActiveServer()
  assert.equal(state.auth.token, null)
  assert.equal(state.auth.user, null)
  assert.equal(getActiveAuthToken(server), null)
  const saved = JSON.parse(storage.get('qibocal_report_auth'))
  assert.equal(saved[server.id], undefined)
  assert.equal(saved[otherServer.id].token, 'other-session')

  await setActiveServer(server)
  assert.equal(isAuthenticated.value, false)
  await loginActiveServer('editor', 'password')
  assert.equal(state.auth.user.username, 'editor')
  assert.equal(canEdit.value, true)
  assert.equal(isAdmin.value, false)
})

test('selecting a server rejects expired tokens and refreshes user roles', async () => {
  let valid = false
  mock.method(globalThis, 'fetch', async url => {
    if (url.endsWith('/api/auth/status')) return json({ auth_enabled: true })
    if (url.endsWith('/api/auth/me')) return valid ? json(viewer) : json({ detail: 'Expired' }, 401)
    assert.fail(`Unexpected request: ${url}`)
  })
  setServerAuth(server, 'expired-session', editor)
  await setActiveServer(server)
  assert.equal(isAuthenticated.value, false)
  assert.equal(getActiveAuthToken(server), null)

  valid = true
  setServerAuth(server, 'valid-session', editor)
  await setActiveServer(server)
  assert.equal(state.auth.user.role, 'viewer')
  assert.equal(canEdit.value, false)
})

test('unavailable authentication status never grants open-mode permissions', async () => {
  mock.method(globalThis, 'fetch', async () => json({ detail: 'Unavailable' }, 503))
  mock.method(console, 'warn', () => {})
  assert.equal(await setActiveServer(server), false)
  assert.equal(state.auth.checked, false)
  assert.equal(canEdit.value, false)
  assert.equal(isAdmin.value, false)
  assert.match(state.auth.errorMessage, /Cannot verify authentication.*First/)
})

test('overlapping auth checks share a request and cannot restore a logged-out session', async () => {
  let resolveMe
  let markMeStarted
  const meStarted = new Promise(resolve => { markMeStarted = resolve })
  const fetchMock = mock.method(globalThis, 'fetch', async url => {
    if (url.endsWith('/api/auth/status')) return json({ auth_enabled: true })
    markMeStarted()
    return new Promise(resolve => { resolveMe = resolve })
  })
  setServerAuth(server, 'viewer-session', viewer)
  const checking = setActiveServer(server)
  const repeated = checkActiveServerAuth(server)
  await meStarted
  assert.equal(fetchMock.mock.callCount(), 2)
  logoutActiveServer()
  resolveMe(json(viewer))
  assert.equal(await checking, false)
  assert.equal(await repeated, false)
  assert.equal(getActiveAuthToken(server), null)
  assert.equal(state.auth.user, null)
})

test('a response from the previously active server cannot overwrite current permissions', async () => {
  let resolveFirst
  mock.method(globalThis, 'fetch', async url => {
    if (url.startsWith(server.url)) {
      return new Promise(resolve => { resolveFirst = resolve })
    }
    return json({ auth_enabled: true })
  })
  const firstCheck = setActiveServer(server)
  assert.equal(await setActiveServer(otherServer), true)
  resolveFirst(json({ auth_enabled: false }))
  assert.equal(await firstCheck, false)
  assert.equal(state.activeServer.id, otherServer.id)
  assert.equal(state.auth.enabled, true)
  assert.equal(canEdit.value, false)
})

test('API rejection removes the persisted session as well as the active session', async () => {
  mock.method(globalThis, 'fetch', async url => url.endsWith('/api/auth/status')
    ? json({ auth_enabled: true })
    : json({ detail: 'Unauthorized' }, 401))
  await setActiveServer(server)
  setServerAuth(server, 'viewer-session', viewer)
  await apiFetch('/api/reports')
  assert.equal(getActiveAuthToken(server), null)
  assert.equal(state.auth.user, null)
})

test('an old server API rejection clears only that server session', async () => {
  let finishRequest
  mock.method(globalThis, 'fetch', async url => {
    if (url.endsWith('/api/auth/status')) return json({ auth_enabled: true })
    if (url.endsWith('/api/auth/me')) return json(viewer)
    return new Promise(resolve => { finishRequest = resolve })
  })
  await setActiveServer(server)
  setServerAuth(server, 'first-session', viewer)
  setServerAuth(otherServer, 'second-session', editor)
  const pending = apiFetch('/api/qibocal', {}, state.activeServer)
  await setActiveServer(otherServer)
  finishRequest(json({ detail: 'Unauthorized' }, 401))
  await pending
  assert.equal(getActiveAuthToken(server), null)
  assert.equal(getActiveAuthToken(otherServer), 'second-session')
  assert.equal(state.auth.token, 'second-session')
  assert.equal(state.auth.errorMessage, '')
})

test('a stale API rejection cannot clear a newly signed-in session', async () => {
  let finishRequest
  mock.method(globalThis, 'fetch', async url => url.endsWith('/api/auth/status')
    ? json({ auth_enabled: true })
    : new Promise(resolve => { finishRequest = resolve }))
  await setActiveServer(server)
  const pending = apiFetch('/api/qibocal')
  setServerAuth(server, 'new-session', editor)
  finishRequest(json({ detail: 'Unauthorized' }, 401))
  await pending
  assert.equal(getActiveAuthToken(server), 'new-session')
  assert.equal(state.auth.token, 'new-session')
  assert.equal(state.auth.errorMessage, '')
})
