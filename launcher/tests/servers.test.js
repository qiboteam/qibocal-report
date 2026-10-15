import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  ADJECTIVES,
  DASHBOARD_ACTIVE_KEY,
  DASHBOARD_SERVERS_KEY,
  SCIENTISTS,
  mergeDashboardServers,
  serverCommand,
  defaultLaunch,
  launchKeys,
  suggestServerName,
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

test('a launch is found under either spelling of the loopback address', () => {
  assert.deepEqual(launchKeys('http://localhost:8000/'), ['http://localhost:8000', 'http://127.0.0.1:8000'])
  assert.deepEqual(launchKeys('http://127.0.0.1:8000'), ['http://127.0.0.1:8000', 'http://localhost:8000'])
  assert.deepEqual(launchKeys('https://reports.example.org'), ['https://reports.example.org'])
  assert.deepEqual(launchKeys(''), [])
})

test('a registered local server can be started without a remembered launch', () => {
  const options = defaultLaunch({ name: 'zen-bohr', url: 'http://localhost:8010' })
  assert.equal(options.mode, 'server')
  assert.equal(options.name, 'zen-bohr')
  assert.equal(options.host, 'localhost')
  assert.equal(options.port, 8010)
  assert.equal(options.register, true)
  assert.equal(options.directory, null, 'the shared directory')
  assert.equal(defaultLaunch({ url: 'https://reports.example.org' }), null, 'not this machine')
  assert.equal(defaultLaunch({ url: '' }), null)
})

test('the next server is named as the command line names its own', () => {
  const [adjective, scientist] = suggestServerName().split('-')
  assert.ok(ADJECTIVES.includes(adjective))
  assert.ok(SCIENTISTS.includes(scientist))
  const first = `${ADJECTIVES[0]}-${SCIENTISTS[0]}`
  assert.notEqual(suggestServerName([first], () => 0), first, 'a name in use is not suggested again')
})

test('a local server is started with a host and a port', () => {
  assert.equal(
    serverCommand({ mode: 'server', directory: '/data/runs', host: 'localhost', port: 8000 }),
    'qibocal report server /data/runs --host localhost --port 8000 --no-auth'
  )
})

test('the name and the registration are passed on, the directory left out when empty', () => {
  assert.equal(
    serverCommand({ mode: 'server', directory: '  ', port: 8000, name: 'Server 1', register: false }),
    "qibocal report server --host localhost --port 8000 --no-auth --name 'Server 1' --no-register"
  )
  assert.equal(
    serverCommand({ mode: 'client', port: 8000, name: 'Server 1', register: false }),
    'qibocal report client --host localhost --port 8000',
    'the client registers nothing, so it takes neither flag'
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
