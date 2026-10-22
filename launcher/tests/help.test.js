import assert from 'node:assert/strict'
import { readdirSync } from 'node:fs'
import { test } from 'node:test'

import { helpPages, helpTarget } from '../src/lib/help.js'

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

test('links lead within the page, to another Help page, to the rest of the documentation in the application, or out', () => {
  assert.deepEqual(helpTarget('#zoom'), { kind: 'anchor', id: 'zoom' })
  assert.deepEqual(helpTarget('user-guide/launcher/servers'), { kind: 'page', name: 'servers', id: null })
  assert.deepEqual(helpTarget('/docs/user-guide/launcher/installation.md#opening-an-unsigned-build'),
    { kind: 'page', name: 'installation', id: 'opening-an-unsigned-build' })
  assert.deepEqual(helpTarget('user-guide/launcher'), { kind: 'page', name: 'index', id: null })
  // Relative to the page, as the Markdown is written for GitHub too.
  assert.deepEqual(helpTarget('servers.md#start', 'agents'), { kind: 'page', name: 'servers', id: 'start' })
  assert.deepEqual(helpTarget('../../reference/cli.md', 'agents'), { kind: 'docs', page: 'reference/cli', id: null })
  // The rest of the documentation is in the application's dashboard; the deployed copy of it too.
  assert.deepEqual(helpTarget('reference/cli'), { kind: 'docs', page: 'reference/cli', id: null })
  assert.deepEqual(helpTarget('https://qibo.science/qibocal-report/#/docs/user-guide/launcher/agents'), { kind: 'page', name: 'agents', id: null })
  assert.deepEqual(helpTarget('https://github.com/qiboteam'), { kind: 'url', url: 'https://github.com/qiboteam' })
})
