import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  NOTEBOOK_FIELDS,
  defaultNotebookOptions,
  describeConnection,
  normalizeNotebookOptions,
  toEditorValues
} from '../src/lib/notebooks.js'

test('the editor starts from the command-line defaults', () => {
  const values = defaultNotebookOptions()
  assert.equal(values.venv, 'qibocal')
  assert.equal(values.marimo, false)
  assert.equal(values.timeout, 300)
  assert.deepEqual(Object.keys(values).sort(), NOTEBOOK_FIELDS.map(field => field.name).sort())
})

test('only the options that differ from the defaults are passed on', () => {
  const { options, valid } = normalizeNotebookOptions({
    ...defaultNotebookOptions(),
    ssh: '  user@login  ',
    queue: 'mychip'
  })
  assert.ok(valid)
  assert.deepEqual(options, { ssh: 'user@login', queue: 'mychip' })
})

test('a stored connection fills the editor back', () => {
  const values = toEditorValues({ ssh: 'user@login', marimo: true })
  assert.equal(values.ssh, 'user@login')
  assert.equal(values.marimo, true)
  assert.equal(values.venv, 'qibocal', 'unset options keep their default')
})

test('subnets with host bits set are refused, like ip_network does', () => {
  const rejected = normalizeNotebookOptions({ ...defaultNotebookOptions(), subnet: '192.168.0.1/24' })
  assert.equal(rejected.valid, false)
  assert.match(rejected.errors.subnet, /192\.168\.0\.0\/24/)

  const accepted = normalizeNotebookOptions({ ...defaultNotebookOptions(), subnet: '192.168.0.0/24' })
  assert.equal(accepted.valid, true)
  assert.equal(accepted.options.subnet, '192.168.0.0/24')
})

test('malformed subnets are refused', () => {
  for (const subnet of ['192.168.0.0', '10.0.0.0/33', '300.1.1.0/24', 'not/a/network']) {
    assert.equal(
      normalizeNotebookOptions({ ...defaultNotebookOptions(), subnet }).valid,
      false,
      `${subnet} should be refused`
    )
  }
})

test('a non-positive timeout is refused', () => {
  const { valid, errors } = normalizeNotebookOptions({ ...defaultNotebookOptions(), timeout: 0 })
  assert.equal(valid, false)
  assert.ok(errors.timeout)
})

test('srun options without a partition warn without blocking', () => {
  const { valid, warnings, options } = normalizeNotebookOptions({
    ...defaultNotebookOptions(),
    slurm: '--time 02:00:00'
  })
  assert.equal(valid, true, 'the session can still be started')
  assert.ok(warnings.slurm)
  assert.equal(options.slurm, '--time 02:00:00')
})

test('connections are described in one line', () => {
  assert.equal(describeConnection({}), 'local session · JupyterLab')
  assert.equal(
    describeConnection({ ssh: 'user@login', queue: 'mychip', marimo: true }),
    'ssh user@login · partition mychip · Marimo'
  )
})
