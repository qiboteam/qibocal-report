import assert from 'node:assert/strict'
import { readdirSync } from 'node:fs'
import { test } from 'node:test'

import { DOCS_URL, helpPages, helpTarget } from '../src/lib/help.js'

test('the Help pages are the Desktop Launcher section of the docs, overview first, each a file', () => {
  const pages = helpPages()
  assert.equal(pages[0].name, 'index')
  assert.ok(pages.some(page => page.name === 'keyboard'), 'the keyboard page carries the live list')
  const files = readdirSync(new URL('../../docs/user-guide/launcher/', import.meta.url))
    .filter(name => name.endsWith('.md'))
    .map(name => name.replace(/\.md$/, ''))
    .sort()
  assert.deepEqual(pages.map(page => page.name).sort(), files, 'no page without a file, no file without a page')
})

test('links lead within the page, to another Help page, or out to the deployed documentation', () => {
  assert.deepEqual(helpTarget('#zoom'), { kind: 'anchor', id: 'zoom' })
  assert.deepEqual(helpTarget('user-guide/launcher/servers'), { kind: 'page', name: 'servers', id: null })
  assert.deepEqual(helpTarget('/docs/user-guide/launcher/installation.md#opening-an-unsigned-build'),
    { kind: 'page', name: 'installation', id: 'opening-an-unsigned-build' })
  assert.deepEqual(helpTarget('user-guide/launcher'), { kind: 'page', name: 'index', id: null })
  assert.deepEqual(helpTarget('reference/cli'), { kind: 'url', url: `${DOCS_URL}reference/cli` })
  assert.deepEqual(helpTarget('https://github.com/qiboteam'), { kind: 'url', url: 'https://github.com/qiboteam' })
})
