import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  addEntry,
  describeEntries,
  emptyDocument,
  entryFields,
  formatDocument,
  parseDocument,
  removeEntry,
  renameEntry,
  shapeOf,
  updateEntry
} from '../src/lib/config.js'

test('an unknown file is treated as a map of entries', () => {
  assert.equal(shapeOf('servers.json').kind, 'list')
  assert.equal(shapeOf('notebooks.json').kind, 'map')
  assert.equal(shapeOf('whatever.json').kind, 'map')
  assert.deepEqual(emptyDocument('servers.json'), [])
  assert.deepEqual(emptyDocument('auth.json'), {})
})

test('a file that was never written parses as empty', () => {
  assert.deepEqual(parseDocument('servers.json', ''), { value: [], error: null, version: null })
  assert.deepEqual(parseDocument('launcher.json', '   \n'), { value: {}, error: null, version: null })
  assert.deepEqual(parseDocument('launcher.json', undefined), { value: {}, error: null, version: null })
})

test('a broken document answers the parser message instead of raising', () => {
  const parsed = parseDocument('servers.json', '[{]')
  assert.equal(parsed.value, null)
  assert.match(parsed.error, /./)
})

test('a document of the wrong shape is refused', () => {
  assert.match(parseDocument('servers.json', '{"a": 1}').error, /list of entries/)
  assert.match(parseDocument('launcher.json', '[]').error, /object of named entries/)
  assert.match(parseDocument('notebooks.json', '[1, 2]').error, /object of named entries/)
  assert.match(parseDocument('notebooks.json', '42').error, /object of named entries/)
})

test('a formatted document carries the version, and ends with a newline', () => {
  assert.equal(formatDocument('servers.json', []), '{\n  "version": 1,\n  "servers": []\n}\n')
  assert.equal(formatDocument('launcher.json', { a: 1 }), '{\n  "version": 1,\n  "a": 1\n}\n')
  assert.deepEqual(JSON.parse(formatDocument('notebooks.json', { c: { ssh: 'x' } })), { version: 1, connections: { c: { ssh: 'x' } } })
})

test('the entries come out of their envelope, versioned or not', () => {
  assert.deepEqual(parseDocument('servers.json', '[{"url": "http://a"}]').value, [{ url: 'http://a' }], 'the file before versions')
  assert.deepEqual(parseDocument('servers.json', '{"version": 1, "servers": [{"url": "http://a"}]}').value, [{ url: 'http://a' }])
  assert.deepEqual(parseDocument('servers.json', '{"version": 1}').value, [], 'an envelope with nothing in it')
  assert.deepEqual(parseDocument('notebooks.json', '{"c": {"ssh": "x"}}').value, { c: { ssh: 'x' } })
  assert.deepEqual(parseDocument('notebooks.json', '{"version": 1, "connections": {"c": {"ssh": "x"}}}').value, { c: { ssh: 'x' } })
  assert.deepEqual(parseDocument('launcher.json', '{"version": 1, "package": "x"}').value, { package: 'x' }, 'the version is not a preference')
  assert.equal(parseDocument('launcher.json', '{"version": 1}').version, 1)
})

test('a file of another version is refused, and says so', () => {
  const parsed = parseDocument('servers.json', '{"version": 2, "servers": []}')
  assert.equal(parsed.value, null)
  assert.equal(parsed.version, 2)
  assert.match(parsed.error, /another version.*format 2; this one reads 1/)
})

test('servers are described by position, connections by name', () => {
  const servers = describeEntries('servers.json', [
    { id: 'srv-1', name: 'Lab', url: 'http://lab:8000' },
    { id: 'srv-2', url: 'http://spare:8000' }
  ])
  assert.deepEqual(servers.map(entry => entry.key), ['0', '1'])
  assert.deepEqual(servers.map(entry => entry.title), ['Lab', 'http://spare:8000'])
  assert.equal(servers[0].subtitle, 'http://lab:8000')

  const connections = describeEntries('notebooks.json', { cluster: { ssh: 'me@node', queue: 'chip' } })
  assert.deepEqual(connections.map(entry => entry.key), ['cluster'])
  assert.equal(connections[0].title, 'cluster')
  assert.equal(connections[0].subtitle, 'ssh me@node · partition chip · JupyterLab')
})

test('a document of the wrong shape describes no entries', () => {
  assert.deepEqual(describeEntries('servers.json', null), [])
  assert.deepEqual(describeEntries('notebooks.json', ['a']), [])
})

test('a server offers its known fields even when it lacks them', () => {
  const fields = entryFields('servers.json', { id: 'srv-1', url: 'http://lab:8000' })
  const named = Object.fromEntries(fields.map(field => [field.name, field]))
  assert.equal(named.name.value, '')
  assert.equal(named.name.type, 'text')
  assert.equal(named.url.value, 'http://lab:8000')
  // Whatever the file also holds stays editable, under its own key.
  assert.equal(named.id.value, 'srv-1')
  assert.deepEqual(fields.slice(0, 4).map(field => field.name), ['name', 'url', 'description', 'avatar'])
})

test('a field is typed by what it holds, not by what it should hold', () => {
  const fields = entryFields('notebooks.json', { ssh: 'me@node', timeout: 120, marimo: true, extra: { a: 1 } })
  const named = Object.fromEntries(fields.map(field => [field.name, field]))
  assert.equal(named.ssh.type, 'text')
  assert.equal(named.timeout.type, 'number')
  assert.equal(named.marimo.type, 'boolean')
  assert.equal(named.extra.type, 'json')
  // An option the connection does not carry is not shown.
  assert.equal(named.queue, undefined)
})

test('a scalar entry becomes a single unnamed field', () => {
  const fields = entryFields('launcher.json', '/usr/bin/qibocal')
  assert.deepEqual(fields, [{ name: '', label: 'Value', type: 'text', value: '/usr/bin/qibocal' }])
})

test('updating a field leaves the rest of the document alone', () => {
  const servers = [{ id: 'srv-1', name: 'Lab' }, { id: 'srv-2', name: 'Spare' }]
  const updated = updateEntry('servers.json', servers, '1', 'name', 'Backup')
  assert.deepEqual(updated, [{ id: 'srv-1', name: 'Lab' }, { id: 'srv-2', name: 'Backup' }])
  assert.deepEqual(servers[1], { id: 'srv-2', name: 'Spare' })

  const notebooks = { cluster: { ssh: 'me@node' } }
  assert.deepEqual(updateEntry('notebooks.json', notebooks, 'cluster', 'queue', 'chip'), {
    cluster: { ssh: 'me@node', queue: 'chip' }
  })
})

test('an unnamed field replaces the whole entry', () => {
  assert.deepEqual(updateEntry('launcher.json', { executable: 'a' }, 'executable', '', 'b'), { executable: 'b' })
})

test('updating an entry that is not there changes nothing', () => {
  const servers = [{ id: 'srv-1' }]
  assert.equal(updateEntry('servers.json', servers, '4', 'name', 'Ghost'), servers)
  assert.deepEqual(updateEntry('notebooks.json', {}, 'absent', 'ssh', 'me@node'), {})
})

test('renaming keeps the entry where it was', () => {
  const notebooks = { first: { ssh: 'a' }, cluster: { ssh: 'b' }, last: { ssh: 'c' } }
  assert.deepEqual(Object.keys(renameEntry('notebooks.json', notebooks, 'cluster', 'chip')), [
    'first',
    'chip',
    'last'
  ])
})

test('a rename that would collide, or empty a name, is refused', () => {
  const notebooks = { cluster: { ssh: 'a' }, chip: { ssh: 'b' } }
  assert.equal(renameEntry('notebooks.json', notebooks, 'cluster', 'chip'), notebooks)
  assert.equal(renameEntry('notebooks.json', notebooks, 'cluster', '  '), notebooks)
  assert.equal(renameEntry('servers.json', [], '0', 'anything').length, 0)
})

test('removing an entry', () => {
  assert.deepEqual(removeEntry('servers.json', [{ id: 'a' }, { id: 'b' }], '0'), [{ id: 'b' }])
  assert.deepEqual(removeEntry('notebooks.json', { a: 1, b: 2 }, 'a'), { b: 2 })
  assert.deepEqual(removeEntry('notebooks.json', null, 'a'), {})
})

test('a new server is appended with the fields the dashboard needs', () => {
  const added = addEntry('servers.json', [{ id: 'srv-1' }])
  assert.equal(added.key, '1')
  assert.equal(added.value.length, 2)
  assert.match(added.value[1].id, /^srv-/)
  assert.equal(added.value[1].avatar, 'quantum-ring')
})

test('a new connection takes a free name', () => {
  const first = addEntry('notebooks.json', {})
  assert.equal(first.key, 'new-connection')
  const second = addEntry('notebooks.json', first.value)
  assert.equal(second.key, 'new-connection-2')
  assert.deepEqual(Object.keys(addEntry('notebooks.json', {}, 'cluster').value), ['cluster'])
})
