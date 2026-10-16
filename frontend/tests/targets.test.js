import assert from 'node:assert/strict'
import { test } from 'node:test'

import { flatQubits, targetKey, targetLabel } from '../src/utils/targets.js'

test('a pair reads as one target and filters as one', () => {
  assert.equal(targetLabel(2), 'Q2')
  assert.equal(targetLabel([2, 3]), 'Q2–Q3')
  assert.equal(targetLabel('D1'), 'QD1')
  assert.equal(targetKey(2), '2')
  assert.equal(targetKey([2, 3]), '2-3')
  assert.deepEqual(flatQubits([0, [2, 3], 3]), [0, 2, 3])
})
