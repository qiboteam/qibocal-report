import assert from 'node:assert/strict'
import { beforeEach, afterEach, test, mock } from 'node:test'

function createStorage() {
  const data = new Map()
  return {
    data,
    getItem: key => data.get(key) ?? null,
    setItem: (key, value) => data.set(key, String(value)),
    removeItem: key => data.delete(key)
  }
}

globalThis.localStorage = createStorage()
globalThis.sessionStorage = createStorage()

const {
  state, addServer, updateServer, deleteServer, fetchServers,
  setActiveServer, setServerAuth, getActiveAuthToken, saveStoredServers,
  exportClientState, importClientState, loginActiveServer, registerWithInvite
} = await import('../src/store.js')
const { parseClientState } = await import('../src/utils/clientState.js')

const first = { id: 'first', name: 'First', url: 'http://first.example' }
const second = { id: 'second', name: 'Second', url: 'http://second.example' }
const user = { id: 'user', username: 'user', role: 'admin' }
const initialSearch = JSON.parse(JSON.stringify(state.searchState))

beforeEach(() => {
  setActiveServer(null)
  setServerAuth(first, null, null)
  setServerAuth(second, null, null)
  localStorage.data.clear()
  sessionStorage.data.clear()
  state.servers = [first, second]
  state.history = []
  state.searchState = structuredClone(initialSearch)
  state.sidebarCollapsed = false
  saveStoredServers(state.servers)
  mock.method(globalThis, 'fetch', async url => {
    assert.ok(url.endsWith('/api/auth/status'), `Unexpected backend request: ${url}`)
    return Response.json({ auth_enabled: false })
  })
})

afterEach(() => mock.restoreAll())

test('registration, customization, ordering and deletion use only browser storage', async () => {
  await setActiveServer(first)
  const added = await addServer({
    url: 'third.example/', name: 'Third',
    author_identities: { Alice: ['alice'] }, protocol_docs: { rabi: '/rabi.md' }
  })
  assert.equal(added.url, 'http://third.example')
  assert.deepEqual(added.protocol_docs, { rabi: '/rabi.md' })
  assert.equal((await addServer('http://third.example')).id, added.id)
  assert.equal(state.servers.length, 3)
  await updateServer(added.id, { name: 'Renamed' })
  const ordered = [state.servers[2], second, first]
  saveStoredServers(ordered)
  state.servers = ordered
  await fetchServers()
  assert.deepEqual(state.servers.map(server => server.id), [added.id, second.id, first.id])
  assert.equal(await deleteServer(first.id), true)
  assert.equal(state.activeServer.id, added.id)
  assert.equal(await deleteServer(second.id), true)
  assert.equal(await deleteServer(added.id), true)
  await fetchServers()
  assert.deepEqual(state.servers, [])
  assert.deepEqual(JSON.parse(localStorage.getItem('qibocal_report_servers')), [])
  assert.equal(state.activeServer, null)
  assert.equal(localStorage.getItem('qibocal_active_server_id'), null)
})

test('a pending status refresh cannot resurrect a deleted server', async () => {
  let resolveStatus
  state.activeServer = first
  mock.method(globalThis, 'fetch', () => new Promise(resolve => { resolveStatus = resolve }))
  const loading = fetchServers()
  await deleteServer(second.id)
  await deleteServer(first.id)
  resolveStatus(Response.json({ auth_enabled: false }))
  await loading
  assert.deepEqual(state.servers, [])
  assert.equal(state.activeServer, null)
  assert.equal(state.auth.user, null)
})

test('changing a server address and deleting a card clear its cached session', async () => {
  setServerAuth(second, 'second-session', user)
  localStorage.setItem('server_connection_second', 'online')
  await updateServer(second.id, { url: 'new.example' })
  assert.equal(getActiveAuthToken(second), null)
  assert.equal(localStorage.getItem('server_connection_second'), null)
  setServerAuth(second, 'new-session', user)
  await deleteServer(second.id)
  assert.equal(getActiveAuthToken(second), null)
})

test('registry writes fail explicitly without changing the displayed registry', async () => {
  const original = JSON.stringify(state.servers)
  mock.method(localStorage, 'setItem', () => { throw new Error('Storage full') })
  await assert.rejects(addServer('third.example'), /Storage full/)
  await assert.rejects(updateServer(first.id, { name: 'Changed' }), /Storage full/)
  await assert.rejects(deleteServer(first.id), /Storage full/)
  assert.equal(JSON.stringify(state.servers), original)
})

test('invalid addresses and duplicate edits are rejected without changing the registry', async () => {
  const original = JSON.stringify(state.servers)
  await assert.rejects(addServer('http://invalid address'))
  await assert.rejects(updateServer(first.id, { url: second.url }), /already registered/)
  await assert.rejects(updateServer(first.id, { url: 'http://invalid address' }))
  assert.equal(JSON.stringify(state.servers), original)
})

test('client state round-trips settings without credentials or transient state', async () => {
  await setActiveServer(second)
  setServerAuth(second, 'secret-session', user)
  state.history = [{
    id: 'report', platform: 'platform', date: null, tags: ['calibration'],
    server_id: second.id, server_url: second.url, opened_at: '2026-09-30'
  }]
  state.searchState.serverId = second.id
  state.searchState.filters.q = 'rabi'
  state.searchState.filters.qubits = ['0', '1']
  state.searchState.currentPage = 3
  state.sidebarCollapsed = true
  state.currentReportData = { sensitive: 'transient' }
  localStorage.setItem('qibocal_sidebar_width', '320')
  localStorage.setItem('qibocal_report_table_columns_v1', '{"platform":160}')
  localStorage.setItem('unrelated-app', 'preserve')
  localStorage.setItem('server_connection_second', 'online')
  const saved = JSON.parse(JSON.stringify(exportClientState()))
  assert.equal(JSON.stringify(saved).includes('secret-session'), false)
  assert.equal(JSON.stringify(saved).includes('transient'), false)
  assert.equal(saved.auth, undefined)
  assert.deepEqual(saved.servers.map(server => server.id), [first.id, second.id])

  state.servers = []
  state.history = []
  state.searchState.filters.q = ''
  localStorage.setItem('qibocal_sidebar_width', '200')
  importClientState(saved)
  assert.deepEqual(exportClientState(), saved)
  assert.equal(state.activeServer.id, second.id)
  assert.equal(getActiveAuthToken(second), null)
  assert.equal(state.auth.checked, false)
  assert.equal(state.auth.user, null)
  assert.equal(state.auth.showLoginModal, false)
  assert.equal(state.currentReportData, null)
  assert.equal(localStorage.getItem('qibocal_report_auth'), null)
  assert.equal(localStorage.getItem('server_connection_second'), null)
  assert.equal(localStorage.getItem('unrelated-app'), 'preserve')
  assert.deepEqual(JSON.parse(sessionStorage.getItem('qibocal_report_search_state')), saved.searchState)
})

test('loading an empty registry replaces previous servers and layout preferences', () => {
  const saved = exportClientState()
  saved.servers = []
  saved.activeServerId = null
  localStorage.setItem('qibocal_sidebar_width', '320')
  importClientState(saved)
  assert.deepEqual(state.servers, [])
  assert.equal(state.activeServer, null)
  assert.equal(localStorage.getItem('qibocal_sidebar_width'), null)
  assert.deepEqual(JSON.parse(localStorage.getItem('qibocal_report_servers')), [])
})

test('invalid client-state files leave existing state and storage untouched', () => {
  const original = exportClientState()
  const persisted = [...localStorage.data]
  for (const corrupt of [
    data => { data.version = 2 },
    data => { data.servers.push(data.servers[0]) },
    data => { data.activeServerId = 'missing' },
    data => { data.servers[0].url = 'javascript:alert(1)' },
    data => { data.searchState.filters.qubits = {} },
    data => { data.searchState.currentPage = -1 },
    data => { data.layout.qibocal_sidebar_width = 'NaN' },
    data => { data.layout.qibocal_report_table_columns_v1 = '{"platform":"wide"}' }
  ]) {
    const invalid = structuredClone(original)
    corrupt(invalid)
    assert.throws(() => importClientState(invalid))
    assert.deepEqual(exportClientState(), original)
    assert.deepEqual([...localStorage.data], persisted)
  }
})

test('unknown fields and authentication storage are excluded from files', () => {
  const saved = exportClientState()
  saved.auth = { token: 'secret' }
  saved.servers[0].token = 'secret'
  saved.history = [{ id: 'report', token: 'secret' }]
  saved.layout.qibocal_report_auth = '{"token":"secret"}'
  const parsed = parseClientState(saved)
  assert.equal(JSON.stringify(parsed).includes('secret'), false)
})

test('failed imports roll back persisted settings before changing reactive state', () => {
  const original = exportClientState()
  const persisted = [...localStorage.data]
  const saved = structuredClone(original)
  saved.servers = [second]
  const setItem = localStorage.setItem
  mock.method(localStorage, 'setItem', (key, value) => {
    if (key === 'qibocal_report_history') throw new Error('Storage full')
    return setItem(key, value)
  })
  assert.throws(() => importClientState(saved), /Storage full/)
  assert.deepEqual(exportClientState(), original)
  assert.deepEqual([...localStorage.data], persisted)
})

test('import invalidates pending authentication checks and preserves signed-out state', async () => {
  let resolveStatus
  state.activeServer = first
  mock.method(globalThis, 'fetch', () => new Promise(resolve => { resolveStatus = resolve }))
  const checking = fetchServers()
  importClientState(exportClientState())
  resolveStatus(Response.json({ auth_enabled: false }))
  await checking
  assert.equal(state.auth.checked, false)
  assert.equal(state.auth.user, null)
})

test('import prevents pending sign-in and invitation responses from restoring credentials', async () => {
  state.activeServer = first
  for (const request of [
    () => loginActiveServer('user', 'password'),
    () => registerWithInvite('invite', 'user', 'password')
  ]) {
    let resolveLogin
    mock.method(globalThis, 'fetch', () => new Promise(resolve => { resolveLogin = resolve }))
    const signingIn = request()
    importClientState(exportClientState())
    resolveLogin(Response.json({ access_token: 'stale-session', user }))
    await assert.rejects(signingIn, /Client state changed/)
    assert.equal(getActiveAuthToken(first), null)
    assert.equal(state.auth.user, null)
  }
})
