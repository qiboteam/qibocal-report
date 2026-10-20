import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  blankForm,
  formFrom,
  formProblems,
  launchFrom,
  ADJECTIVES,
  DASHBOARD_ACTIVE_KEY,
  DASHBOARD_SERVERS_KEY,
  SCIENTISTS,
  mergeDashboardServers,
  serverCommand,
  upgradeCommand,
  defaultLaunch,
  launchKeys,
  suggestServerName,
  syncDashboardServers,
  toDashboardServer,
  withoutTransient
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

test('merging matches on the address; servers.json is the list, the cache only lends', () => {
  const existing = [
    { id: 'gone', name: 'Remote', url: 'https://reports.example.org', author_identities: { a: ['me'] } },
    { id: 'shared', name: 'Stale name', url: 'http://localhost:8000', protocol_docs: { t1: 'doc' } }
  ]
  const merged = mergeDashboardServers(
    [
      { id: 'ignored', name: 'Fresh name', url: 'http://localhost:8000/' },
      { id: 'twin', name: 'Fresh name', url: 'http://localhost:8000' }
    ],
    existing
  )

  assert.equal(merged.length, 1, 'a cached server the file no longer has does not come back, and a twin address is one')
  const shared = merged[0]
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
})

test('the developer mode carries the frontend port', () => {
  assert.equal(
    serverCommand({ mode: 'dev', directory: '/data', port: 8000, auth: true, frontendPort: 5174 }),
    'qibocal report dev /data --host localhost --port 8000 --auth --frontend-port 5174'
  )
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

test('an update is a command of its own, for a server on another machine', () => {
  assert.equal(
    upgradeCommand({ ssh: 'me@node', venv: 'chip', install: 'qibocal-report==1.2' }),
    'qibocal report server upgrade --ssh me@node --venv chip --install qibocal-report==1.2'
  )
  assert.equal(upgradeCommand({ mode: 'server', host: 'localhost' }), '', 'nothing remote, nothing to upgrade')
  assert.ok(!serverCommand({ mode: 'server', ssh: 'me@node' }).includes('upgrade'), 'starting is not updating')
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

test('the form of a remembered SSH launch opens on another machine, with the entry on top', () => {
  const remembered = {
    mode: 'server', name: 'old-name', register: false, directory: '/data', host: 'localhost', port: 8000,
    auth: true, frontendPort: null, ssh: 'me@cluster', venv: 'qibocal', workdir: null, install: null
  }
  const server = { name: 'quiet-curie', url: 'http://localhost:43210', description: 'On the cluster' }
  const opened = formFrom(remembered, server)
  assert.equal(opened.where, 'ssh')
  assert.equal(opened.form.name, 'quiet-curie')
  assert.equal(opened.form.description, 'On the cluster')
  assert.equal(opened.form.url, 'http://localhost:43210')
  assert.equal(opened.form.ssh, 'me@cluster')
  assert.equal(opened.form.directory, '/data')
  assert.equal(opened.form.auth, true)
  assert.equal(opened.form.workdir, '')
})

test('a server the launcher does not start opens as already running', () => {
  const opened = formFrom(null, { name: 'far', url: 'https://lab.example.org' })
  assert.equal(opened.where, 'reachable')
  assert.equal(opened.form.url, 'https://lab.example.org')
  assert.equal(opened.form.port, 8000, 'the rest is at its default')
})

test('the form and the launch options are each other\'s inverse', () => {
  const form = { ...blankForm(), name: 'brave-bohr', ssh: 'me@cluster', directory: '/data', install: 'qibocal-report==1.2' }
  const options = launchFrom('ssh', form, { register: true })
  assert.equal(options.mode, 'server')
  assert.equal(options.register, true)
  assert.equal(options.ssh, 'me@cluster')
  assert.equal(options.install, 'qibocal-report==1.2')
  assert.equal(options.venv, null)
  assert.deepEqual(formFrom(options).form, { ...form, description: '', url: '' })
  assert.equal(launchFrom('reachable', form), null, 'nothing to start for an address')
  assert.equal(launchFrom('local', { ...blankForm(), name: '' }, { name: 'drawn' }).name, 'drawn')
})

test('what is wrong with a form is said by field', () => {
  assert.deepEqual(formProblems('ssh', { ...blankForm() }), { ssh: 'Name the machine to reach, as ssh would.' })
  assert.deepEqual(formProblems('local', { ...blankForm(), port: 70000 }), { port: 'Enter a port between 1 and 65535.' })
  assert.deepEqual(formProblems('reachable', { ...blankForm() }), {}, 'an empty address is not yet a problem')
  assert.deepEqual(formProblems('reachable', { ...blankForm(), url: 'not an address' }), { url: 'Enter the address of the report server.' })
  assert.deepEqual(formProblems('local', { ...blankForm() }, { entry: true }), { url: 'Enter the address of the report server.' }, 'a registered entry needs one')
  assert.deepEqual(formProblems('local', { ...blankForm(), url: 'localhost:8000' }, { entry: true }), {})
})

test('servers shown for a look are in the dashboard, and out of what it saves', () => {
  const storage = new Map()
  const store = { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key) }
  const shown = syncDashboardServers([{ name: 'QRC', url: 'http://127.0.0.1:8000' }], {
    storage: store,
    transient: [{ name: 'chip reports', url: 'http://127.0.0.1:9000' }]
  })
  assert.deepEqual(shown.map(server => server.url), ['http://127.0.0.1:8000', 'http://127.0.0.1:9000'])
  const saved = withoutTransient(shown, store)
  assert.deepEqual(saved.map(server => server.url), ['http://127.0.0.1:8000'], 'never written to servers.json')
  syncDashboardServers([{ name: 'QRC', url: 'http://127.0.0.1:8000' }], { storage: store })
  assert.equal(withoutTransient(shown, store).length, 2, 'gone from the list once it stops: nothing left to hold back')
})
