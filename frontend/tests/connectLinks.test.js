import assert from 'node:assert/strict'
import { test } from 'node:test'

import { connectAddress, connectLink } from '../src/utils/url.js'

test('a connect link carries the server, and only an http(s) address is taken from one', () => {
  assert.equal(
    connectLink('https://reports.example.org/', { base: 'https://qibo.science/qibocamp' }),
    'https://qibo.science/qibocamp/#/connect?server=https%3A%2F%2Freports.example.org'
  )
  assert.equal(connectAddress('https://reports.example.org/prefix/'), 'https://reports.example.org/prefix')
  assert.equal(connectAddress('http://lab:8000'), 'http://lab:8000')
  assert.equal(connectAddress('http://lab:8000/?x=1#y'), 'http://lab:8000', 'no query, no fragment')
  for (const value of ['javascript:alert(1)', 'lab:8000', 'ftp://lab', 'http://user:pw@lab', '', undefined, ['http://lab']]) {
    assert.equal(connectAddress(value), '', String(value))
  }
})
