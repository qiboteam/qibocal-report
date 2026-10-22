import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  THIS_MACHINE,
  destinationUses,
  machineFor,
  machineLabel,
  machineList,
  machineNameError,
  migrateAgentRemotes,
  retargetAgents,
  retargetConnections,
  retargetHosts,
  retargetLaunches,
  unnamedDestinations,
  usesOf,
  withMachine,
  withoutMachine
} from '../src/lib/machines.js'

test('machines are named destinations, and a destination is shown by its machine', () => {
  let machines = withMachine({}, 'lab', ' me@login ')
  machines = withMachine(machines, 'cluster', 'cluster')
  assert.deepEqual(machineList(machines), [{ name: 'cluster', ssh: 'cluster' }, { name: 'lab', ssh: 'me@login' }])
  const list = machineList(machines)
  assert.equal(machineFor('me@login', list).name, 'lab')
  assert.equal(machineFor('', list), null)
  assert.equal(machineLabel('me@login', list), 'lab')
  assert.equal(machineLabel('elsewhere', list), 'elsewhere', 'unnamed: the destination itself')
  assert.equal(machineLabel(null, list), THIS_MACHINE)
  assert.match(machineNameError('lab', machines), /already/)
  assert.match(machineNameError(' lab', machines), /spaces/)
  assert.equal(machineNameError('new-one', machines), '')
  assert.deepEqual(Object.keys(withoutMachine(machines, 'lab')), ['cluster'])
})

test('every use of a destination is found, and the destinations no machine names', () => {
  const uses = destinationUses({
    notebooks: { chip: { ssh: 'me@login' }, here: {} },
    remotes: { onsite: { ssh: 'me@login' } },
    agents: { agents: { tuna: { ssh: 'cluster' } } },
    hosts: { lab: { agents: { kept: { platform: 'x' } } } },
    launches: { 'http://localhost:9000': { ssh: 'me@login' }, 'http://localhost:8000': { ssh: null } },
    servers: [{ name: 'lab reports', url: 'http://localhost:9000/' }]
  })
  const list = machineList({ lab: { ssh: 'me@login' } })
  assert.deepEqual(usesOf(list[0], uses).map(use => [use.kind, use.name]),
    [['notebook', 'chip'], ['remote', 'onsite'], ['kept', 'kept'], ['server', 'lab reports']])
  assert.deepEqual(unnamedDestinations(uses, list), ['cluster'])
})

test('a destination moves in every file that stores it, and nothing else does', () => {
  assert.deepEqual(retargetConnections({ a: { ssh: 'old', queue: 'q' }, b: { ssh: 'other' } }, 'old', 'new'),
    { a: { ssh: 'new', queue: 'q' }, b: { ssh: 'other' } })
  assert.deepEqual(retargetAgents({ agents: { a: { ssh: 'old' } } }, 'old', 'new'), { agents: { a: { ssh: 'new' } } })
  assert.deepEqual(retargetHosts({ lab: { agents: { a: { ssh: 'old' } } } }, 'old', 'new'), { lab: { agents: { a: { ssh: 'new' } } } })
  assert.deepEqual(retargetLaunches({ 'http://x': { ssh: 'old', port: 1 } }, 'old', 'new'), { 'http://x': { ssh: 'new', port: 1 } })
})

test('the agent remotes become machines once, and keep their configurations', () => {
  const hosts = {
    lab: { ssh: 'me@login', agents: { onsite: { platform: 'qw5q' } } },
    'old@host': { agents: {} },
    cluster: { ssh: 'cluster2', agents: {} }
  }
  const { machines, hosts: kept, changed } = migrateAgentRemotes({ cluster: { ssh: 'cluster' } }, hosts)
  assert.equal(changed, true)
  assert.deepEqual(machines, { cluster: { ssh: 'cluster' }, lab: { ssh: 'me@login' }, 'old@host': { ssh: 'old@host' } },
    'a name taken already stays as it is; a remote keyed by its destination keeps it')
  assert.deepEqual(kept, { lab: { agents: { onsite: { platform: 'qw5q' } } }, 'old@host': { agents: {} }, cluster: { agents: {} } })
  assert.equal(migrateAgentRemotes(machines, kept).changed, false, 'once')
})

test('a list is filtered by machine: this one, a named one, or an unnamed destination', async () => {
  const { machineOptions, onMachine } = await import('../src/lib/machines.js')
  const list = machineList({ lab: { ssh: 'me@login' } })
  assert.deepEqual(machineOptions(['me@login', '', 'cluster', 'me@login'], list).map(option => option.value), ['all', 'local', 'cluster', 'lab'])
  assert.deepEqual(machineOptions(['me@login'], list).map(option => option.value), ['all', 'lab'], 'no this machine when none is here')
  assert.equal(onMachine('me@login', 'lab', list), true)
  assert.equal(onMachine('', 'lab', list), false)
  assert.equal(onMachine('', 'local', list), true)
  assert.equal(onMachine('cluster', 'cluster', list), true)
  assert.equal(onMachine('anything', 'all', list), true)
})
