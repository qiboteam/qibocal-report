import assert from 'node:assert/strict'
import { test } from 'node:test'

import { createArrivals, describeArrivals } from '../src/utils/arrivals.js'

test('reports count as new from the second sight on, and only upwards', () => {
  const arrivals = createArrivals()
  assert.equal(arrivals('a', 10), 0, 'the first sight is a baseline')
  assert.equal(arrivals('a', 10), 0)
  assert.equal(arrivals('a', 13), 3)
  assert.equal(arrivals('a', 11), 0, 'deletions are not arrivals')
  assert.equal(arrivals('a', 12), 1)
  assert.equal(arrivals('b', 5), 0, 'each server on its own')
  assert.equal(arrivals('a', NaN), 0)
  assert.equal(arrivals('a', 12), 0, 'nonsense leaves the baseline alone')
})

test('the sentence counts', () => {
  assert.equal(describeArrivals(1, 'QRC'), '1 new report on QRC.')
  assert.equal(describeArrivals(4, 'QRC'), '4 new reports on QRC.')
})
