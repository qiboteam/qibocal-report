import assert from 'node:assert/strict'
import { test } from 'node:test'

import { ZOOM_LEVELS, describeZoom, parseZoom, stepZoom, zoomRequest } from '../src/lib/zoom.js'

test('the zoom steps through the levels and stops at the ends', () => {
  assert.equal(stepZoom(1, 1), 1.1)
  assert.equal(stepZoom(1, -1), 0.9)
  assert.equal(stepZoom(ZOOM_LEVELS[ZOOM_LEVELS.length - 1], 1), ZOOM_LEVELS[ZOOM_LEVELS.length - 1])
  assert.equal(stepZoom(ZOOM_LEVELS[0], -1), ZOOM_LEVELS[0])
  assert.equal(stepZoom(1.05, 1), 1.1, 'a level between two steps goes to the next one')
  assert.equal(stepZoom('garbage', 1), 1.1, 'nonsense counts as the default')
})

test('a stored level is read back, nonsense as the default', () => {
  assert.equal(parseZoom('1.25'), 1.25)
  assert.equal(parseZoom(null), 1)
  assert.equal(parseZoom('42'), 1)
  assert.equal(describeZoom(1.25), '125%')
  assert.equal(describeZoom(undefined), '100%')
})

test('the keys ask for a step or a reset, with the command or control key only', () => {
  assert.equal(zoomRequest({ metaKey: true, key: '=' }), 'in')
  assert.equal(zoomRequest({ ctrlKey: true, key: '+' }), 'in')
  assert.equal(zoomRequest({ ctrlKey: true, key: '-' }), 'out')
  assert.equal(zoomRequest({ metaKey: true, key: '0' }), 'reset')
  assert.equal(zoomRequest({ key: '+' }), null, 'a bare plus is typing')
  assert.equal(zoomRequest({ metaKey: true, altKey: true, key: '+' }), null)
  assert.equal(zoomRequest({ metaKey: true, key: 'k' }), null)
})
