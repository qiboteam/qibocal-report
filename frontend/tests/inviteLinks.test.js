import assert from 'node:assert/strict'
import { test } from 'node:test'

import { DEPLOYED_DASHBOARD, dashboardBase, inviteLink, parseServerAndInvite } from '../src/utils/url.js'

test('a link opens this dashboard on the web, the deployed one from the application', () => {
  assert.equal(dashboardBase({ protocol: 'https:', origin: 'https://qibo.science', pathname: '/qibocamp/' }), 'https://qibo.science/qibocamp')
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

test('a plain server address has no token, and nor do other link forms', () => {
  assert.deepEqual(parseServerAndInvite('lab:8000/'), { url: 'http://lab:8000', inviteToken: null, resetToken: null })
  assert.deepEqual(parseServerAndInvite('https://lab.example/reports'), { url: 'https://lab.example', inviteToken: null, resetToken: null })
  for (const link of ['http://lab:8000/?invite=abc', 'http://lab:8000/invite/abc', 'http://lab:8000/#/invite?invite_token=abc']) {
    assert.deepEqual(parseServerAndInvite(link), { url: 'http://lab:8000', inviteToken: null, resetToken: null }, link)
  }
})
