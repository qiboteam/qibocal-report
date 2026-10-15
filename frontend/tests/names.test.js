import assert from 'node:assert/strict'
import { test } from 'node:test'

import { ADJECTIVES, SCIENTISTS, generateServerName } from '../src/utils/names.js'

test('a generated name is an adjective and a scientist', () => {
  const [adjective, scientist, ...rest] = generateServerName().split('-')
  assert.ok(ADJECTIVES.includes(adjective))
  assert.ok(SCIENTISTS.includes(scientist))
  assert.deepEqual(rest, [])
})

test('names in use are avoided', () => {
  const sequence = [0, 0, 0, 0, 0.5, 0.5]
  const random = () => sequence.shift() ?? 0.5
  const first = `${ADJECTIVES[0]}-${SCIENTISTS[0]}`
  assert.equal(generateServerName([first, ' '], random), `${ADJECTIVES[7]}-${SCIENTISTS[6]}`)
})

test('an exhausted list falls back to a numbered name', () => {
  const stuck = `${ADJECTIVES[0]}-${SCIENTISTS[0]}`
  assert.equal(generateServerName([stuck, `${stuck}-2`], () => 0), `${stuck}-3`)
})
