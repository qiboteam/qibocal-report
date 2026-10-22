import assert from 'node:assert/strict'
import { readdirSync, statSync } from 'node:fs'
import { test } from 'node:test'

import { DEFAULT_DOCS_NAV, docPages, resolveDocLink } from '../src/utils/docsNav.js'

/** The pages the docs folder holds, by path, as the navigation names them. */
function files(folder = new URL('../../docs/', import.meta.url), prefix = '') {
  return readdirSync(folder).flatMap(name => {
    const path = new URL(name, folder)
    if (statSync(path).isDirectory()) return files(new URL(`${name}/`, folder), `${prefix}${name}/`)
    return name.endsWith('.md') ? [`${prefix}${name}`.replace(/\.md$/, '').replace(/\/index$/, '')] : []
  })
}

test('the navigation lists every page the dashboard carries, and no other', () => {
  // The dashboard reads no server for its documentation: what it carries is all there is.
  assert.deepEqual([...docPages()].sort(), files().sort())
})

test('a link leads to a page of this documentation, from its root or from the page, or outside', () => {
  const doc = (page, id = null) => ({ kind: 'doc', page, id })
  assert.deepEqual(resolveDocLink('#zoom', 'user-guide/reports'), { kind: 'anchor', id: 'zoom' })
  // From the root, as the dashboard writes them.
  assert.deepEqual(resolveDocLink('user-guide/launcher/servers', 'index'), doc('user-guide/launcher/servers'))
  assert.deepEqual(resolveDocLink('/docs/reference/cli.md#env', 'index'), doc('reference/cli', 'env'))
  // From the page's own file, as on GitHub.
  assert.deepEqual(resolveDocLink('../reference/cli.md', 'user-guide/reports'), doc('reference/cli'))
  assert.deepEqual(resolveDocLink('../../reference/api.md#uploading-a-report-by-hand', 'user-guide/launcher/agents'),
    doc('reference/api', 'uploading-a-report-by-hand'))
  assert.deepEqual(resolveDocLink('servers.md', 'user-guide/launcher/agents'), doc('user-guide/launcher/servers'))
  assert.deepEqual(resolveDocLink('quickstart.md', 'user-guide'), doc('user-guide/quickstart'), 'a section is its index')
  assert.deepEqual(resolveDocLink('user-guide/index.md', 'index'), doc('user-guide'))
  // The deployed copy of this very documentation is this documentation.
  assert.deepEqual(resolveDocLink('https://qibo.science/qibocal-report/#/docs/user-guide/launcher/agents', 'index'),
    doc('user-guide/launcher/agents'))
  for (const href of ['https://qibo.science/qibocal/stable/protocols/', 'https://github.com/qiboteam', 'mailto:a@b.c', '//cdn.example/x']) {
    assert.deepEqual(resolveDocLink(href, 'index'), { kind: 'url', url: href })
  }
  assert.ok(DEFAULT_DOCS_NAV.length)
})
