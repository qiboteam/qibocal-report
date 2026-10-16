import assert from 'node:assert/strict'
import { test } from 'node:test'

import { processNews, unattended } from '../src/lib/alerts.js'

test('the user is away when the window is hidden or behind, or another page shows', () => {
  assert.equal(unattended({ hidden: true, focused: true, hash: '#/processes', page: '/processes' }), true)
  assert.equal(unattended({ hidden: false, focused: false, hash: '#/processes', page: '/processes' }), true)
  assert.equal(unattended({ focused: true, hash: '#/processes?process=p1', page: '/processes' }), false)
  assert.equal(unattended({ focused: true, hash: '#/servers', page: '/processes' }), true)
  assert.equal(unattended({ focused: true, hash: '#/dashboard', page: '/dashboard' }), false)
  assert.equal(unattended({ focused: true, hash: '#/report/x', page: '/dashboard' }), true)
  assert.equal(unattended({ focused: true, hash: '#/anything' }), false, 'without a page only the window counts')
})

test('a process has news when it comes up or fails, once', () => {
  const server = { id: 'p', kind: 'server', label: 'QRC', status: 'running', url: 'http://127.0.0.1:1234' }
  assert.deepEqual(processNews(null, server), { title: 'QRC is up', body: 'QRC answers at http://127.0.0.1:1234.' })
  assert.deepEqual(processNews({ ...server, url: null }, server).title, 'QRC is up')
  assert.equal(processNews(server, server), null, 'already up: nothing new')
  assert.equal(processNews(null, { ...server, url: null }), null, 'running without an address yet')
  const failed = { ...server, status: 'failed' }
  assert.equal(processNews(server, failed).title, 'QRC failed')
  assert.equal(processNews(failed, failed), null)
  assert.equal(processNews(null, { kind: 'setup', label: 'Installing', status: 'running', url: null }), null)
})
