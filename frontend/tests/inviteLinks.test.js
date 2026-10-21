import assert from 'node:assert/strict'
import { test } from 'node:test'

import { DEPLOYED_DASHBOARD, dashboardBase, inviteLink, parseServerAndInvite } from '../src/utils/url.js'

test('a link opens this dashboard on the web, the deployed one from the application', () => {
  assert.equal(dashboardBase({ protocol: 'https:', origin: 'https://qibo.science', pathname: '/qibocal-report/' }), 'https://qibo.science/qibocal-report')
  assert.equal(dashboardBase({ protocol: 'http:', origin: 'http://localhost:5173', pathname: '/' }), 'http://localhost:5173')
  assert.equal(dashboardBase({ protocol: 'tauri:', origin: 'tauri://localhost', pathname: '/dashboard.html' }), DEPLOYED_DASHBOARD)
})

test('an invitation link names the token and the server, and reads back', () => {
  const link = inviteLink('http://lab:8000/', 'abc', { base: DEPLOYED_DASHBOARD })
  assert.equal(link, `${DEPLOYED_DASHBOARD}/#/invite?token=abc&server=http%3A%2F%2Flab%3A8000`)
  assert.deepEqual(parseServerAndInvite(link), { url: 'http://lab:8000', inviteToken: 'abc', resetToken: null },
    'pasted in the connect bar: the server it names, not the dashboard')
  const reset = inviteLink('http://lab:8000', 'xyz', { reset: true, base: DEPLOYED_DASHBOARD })
  assert.deepEqual(parseServerAndInvite(reset), { url: 'http://lab:8000', inviteToken: null, resetToken: 'xyz' })
})

test('older forms still read', () => {
  assert.deepEqual(parseServerAndInvite('server=http://lab:8000&invite_token=abc'), { url: 'http://lab:8000', inviteToken: 'abc', resetToken: null })
  assert.equal(parseServerAndInvite('http://lab:8000/#/invite?token=abc').url, 'http://lab:8000')
})
