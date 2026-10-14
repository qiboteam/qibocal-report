import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  DASHBOARD_ACTIVE_KEY,
  DASHBOARD_SERVERS_KEY,
  mergeDashboardServers,
  serverCommand,
  syncDashboardServers,
  toDashboardServer
} from '../src/lib/servers.js'

function createStorage(initial = {}) {
  const data = new Map(Object.entries(initial))
  return {
    data,
    getItem: key => data.get(key) ?? null,
    setItem: (key, value) => data.set(key, String(value)),
    removeItem: key => data.delete(key)
  }
}

test('a configured server becomes a dashboard entry', () => {
  const server = toDashboardServer({ id: 'srv-1', name: 'Local', url: 'http://localhost:8000/' })
  assert.equal(server.id, 'srv-1')
  assert.equal(server.name, 'Local')
  assert.equal(server.url, 'http://localhost:8000')
  assert.deepEqual(server.author_identities, {})
})

test('entries without a usable address are dropped', () => {
  assert.equal(toDashboardServer({ url: '   ' }), null)
  assert.equal(toDashboardServer({ url: 'https://' }), null)
  assert.equal(toDashboardServer(null), null)
  assert.deepEqual(mergeDashboardServers([{ url: '' }, null], []), [])
})

test('a bare host is accepted, as the dashboard accepts it', () => {
  assert.equal(toDashboardServer({ url: 'lab-machine:8000' }).url, 'http://lab-machine:8000')
  assert.equal(toDashboardServer({ url: 'http://[::1]:8000/' }).url, 'http://[::1]:8000')
})

test('merging matches on the address and keeps dashboard-only servers', () => {
  const existing = [
    { id: 'kept', name: 'Remote', url: 'https://reports.example.org', author_identities: { a: ['me'] } },
    { id: 'shared', name: 'Stale name', url: 'http://localhost:8000', protocol_docs: { t1: 'doc' } }
  ]
  const merged = mergeDashboardServers(
    [{ id: 'ignored', name: 'Fresh name', url: 'http://localhost:8000/' }],
    existing
  )

  assert.equal(merged.length, 2)
  assert.equal(merged[0].id, 'kept')
  const shared = merged[1]
  assert.equal(shared.id, 'shared', 'the identifier the dashboard already uses survives')
  assert.equal(shared.name, 'Fresh name', 'the label is refreshed from the configuration')
  assert.deepEqual(shared.protocol_docs, { t1: 'doc' }, 'dashboard-only data is preserved')
})

test('exactly one server is marked as the default', () => {
  const merged = mergeDashboardServers(
    [{ url: 'http://a.example' }, { url: 'http://b.example' }],
    []
  )
  assert.deepEqual(merged.map(server => server.is_default), [true, false])
})

test('synchronising publishes the servers and selects the preferred one', () => {
  const storage = createStorage()
  const servers = syncDashboardServers(
    [{ id: 'one', url: 'http://one.example' }, { id: 'two', url: 'http://two.example' }],
    { storage, preferredUrl: 'http://two.example/' }
  )

  assert.deepEqual(JSON.parse(storage.getItem(DASHBOARD_SERVERS_KEY)), servers)
  assert.equal(storage.getItem(DASHBOARD_ACTIVE_KEY), 'two')
})

test('an existing selection is respected when none is preferred', () => {
  const storage = createStorage({ [DASHBOARD_ACTIVE_KEY]: 'two' })
  syncDashboardServers([{ id: 'one', url: 'http://one.example' }, { id: 'two', url: 'http://two.example' }], { storage })
  assert.equal(storage.getItem(DASHBOARD_ACTIVE_KEY), 'two')
})

test('the selection is cleared when no server is left', () => {
  const storage = createStorage({ [DASHBOARD_ACTIVE_KEY]: 'gone' })
  syncDashboardServers([], { storage })
  assert.equal(storage.getItem(DASHBOARD_ACTIVE_KEY), null)
})

test('unreadable storage does not stop the synchronisation', () => {
  const storage = createStorage({ [DASHBOARD_SERVERS_KEY]: '{not json' })
  const servers = syncDashboardServers([{ id: 'one', url: 'http://one.example' }], { storage })
  assert.equal(servers.length, 1)
  assert.equal(storage.getItem(DASHBOARD_ACTIVE_KEY), 'one')
})

test('a local server is started with a host and a port', () => {
  assert.equal(
    serverCommand({ mode: 'server', directory: '/data/runs', host: 'localhost', port: 8000 }),
    'qibocal report server /data/runs --host localhost --port 8000 --no-auth'
  )
})

test('the developer mode carries the frontend port, the client no directory', () => {
  assert.equal(
    serverCommand({ mode: 'dev', directory: '/data', port: 8000, auth: true, frontendPort: 5174 }),
    'qibocal report dev /data --host localhost --port 8000 --auth --frontend-port 5174'
  )
  assert.equal(serverCommand({ mode: 'client', port: 9000 }), 'qibocal report client --host localhost --port 9000')
})

test('a remote server replaces the address with the SSH options', () => {
  assert.equal(
    serverCommand({
      mode: 'server',
      directory: '/shared/runs',
      port: 8000,
      auth: true,
      ssh: 'me@login-node',
      venv: 'qibocal',
      workdir: '/shared',
      install: 'qibocal-report',
      timeout: 600
    }),
    'qibocal report server /shared/runs --auth --ssh me@login-node ' +
      '--workdir /shared --venv qibocal --install qibocal-report --timeout 600'
  )
})

test('the remote options are left out without a destination', () => {
  assert.equal(
    serverCommand({ mode: 'server', directory: '/data', port: 8000, ssh: '  ', venv: 'qibocal' }),
    'qibocal report server /data --host localhost --port 8000 --no-auth'
  )
})

test('an argument that would be split is quoted', () => {
  assert.equal(
    serverCommand({ mode: 'server', directory: '/data/my runs', port: 8000, ssh: '-J bastion me@node' }),
    "qibocal report server '/data/my runs' --no-auth --ssh '-J bastion me@node'"
  )
})
