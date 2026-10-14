import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  DEFAULT_SPEC,
  archiveSpec,
  describeSpec,
  parseRefs,
  parseReleases,
  parseSpec,
  releaseSpec,
  versionOptions
} from '../src/lib/versions.js'

test('the default is the main branch, installed from its archive', () => {
  assert.equal(
    DEFAULT_SPEC,
    'qibocal-report @ https://github.com/qiboteam/qibocal-report/archive/refs/heads/main.tar.gz'
  )
  assert.deepEqual(parseSpec(DEFAULT_SPEC), { kind: 'branch', ref: 'main' })
  assert.deepEqual(parseSpec(''), { kind: 'branch', ref: 'main' }, 'nothing chosen is the default')
})

test('releases, tags and hand-typed requirements are told apart', () => {
  assert.deepEqual(parseSpec(releaseSpec('0.2.0')), { kind: 'release', ref: '0.2.0' })
  assert.deepEqual(parseSpec(archiveSpec('tag', 'v0.1.0')), { kind: 'tag', ref: 'v0.1.0' })
  assert.deepEqual(parseSpec(archiveSpec('branch', 'feature/x')), { kind: 'branch', ref: 'feature/x' })
  assert.deepEqual(parseSpec('/home/me/checkout'), { kind: 'other', ref: '/home/me/checkout' })
})

test('a requirement is described briefly', () => {
  assert.equal(describeSpec(releaseSpec('0.2.0')), '0.2.0 (PyPI)')
  assert.equal(describeSpec(DEFAULT_SPEC), 'branch main')
  assert.equal(describeSpec(archiveSpec('tag', 'v1')), 'tag v1')
  assert.equal(describeSpec('  something==1 '), 'something==1')
})

test('releases come newest first, yanked ones left out', () => {
  const document = {
    releases: {
      '0.1.0': [{ yanked: false }],
      '0.10.0': [{ yanked: false }],
      '0.2.0': [{ yanked: true }],
      '0.3.0rc1': [{}],
      '0.0.1': []
    }
  }
  assert.deepEqual(parseReleases(document), ['0.10.0', '0.3.0rc1', '0.1.0'])
  assert.deepEqual(parseReleases(null), [])
})

test('main leads the branches, the rest keep their order', () => {
  assert.deepEqual(parseRefs([{ name: 'feature/b' }, { name: 'main' }, { name: 'dev' }, {}]), ['main', 'feature/b', 'dev'])
})

test('the picker keeps the current choice even when the lists lack it', () => {
  const options = versionOptions({ releases: ['0.1.0'], branches: ['main'], tags: [], current: archiveSpec('tag', 'v9') })
  assert.deepEqual(options.map(option => option.label), ['0.1.0 (PyPI)', 'branch main', 'tag v9'])
  const known = versionOptions({ branches: ['main'], current: DEFAULT_SPEC })
  assert.equal(known.length, 1, 'a choice the lists know is not repeated')
})
