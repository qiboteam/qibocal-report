import assert from 'node:assert/strict'
import { test } from 'node:test'

import { describeNodes, describeOccupation, filterJobs, isOwnJob, jobIdFromLog, jobNameFromLog, ownJobs, positionOf, queueKey, queueOf } from '../src/lib/slurm.js'

test('a session names its queue by host and partition', () => {
  assert.equal(queueOf({ ssh: 'me@cluster', queue: 'gpu' }).partition, 'gpu')
  assert.equal(queueKey(queueOf({ ssh: 'me@cluster', queue: 'gpu' })), 'me@cluster|gpu')
  assert.equal(queueKey(queueOf({ queue: 'cpu' })), 'local|cpu')
  assert.equal(queueOf({ ssh: 'me@cluster' }), null, 'no partition, no queue')
})

test('the job id is read off the worker panel the command line printed', () => {
  const lines = [
    '│ Compute node                      │',
    '[1mSLURM_JOB_ID[0m   [0m48213[0m',
    'SLURM_JOB_PARTITION  gpu'
  ]
  assert.equal(jobIdFromLog(lines), '48213')
  assert.equal(jobIdFromLog(['nothing here']), null)
})

const JOBS = [
  { id: '1', name: 'train', user: 'ann', state: 'RUNNING', nodes: 'n01', reason: '' },
  { id: '2', name: 'qibocal', user: 'me', state: 'PENDING', nodes: '', reason: 'Priority' },
  { id: '3', name: 'other', user: 'bob', state: 'PENDING', nodes: '', reason: 'Resources' }
]

test('jobs are filtered by owner, state and text, ours first', () => {
  assert.deepEqual(filterJobs(JOBS, { mine: true, user: 'me' }).map(job => job.id), ['2'])
  assert.deepEqual(filterJobs(JOBS, { states: ['pending'] }).map(job => job.id), ['2', '3'])
  assert.deepEqual(filterJobs(JOBS, { search: 'resources' }).map(job => job.id), ['3'])
  assert.deepEqual(filterJobs(JOBS, { jobId: '3' }).map(job => job.id), ['3', '1', '2'])
  assert.equal(positionOf(JOBS, '3'), 2)
  assert.equal(positionOf(JOBS, '1'), null, 'a running job is not in line')
})

test('the nodes read as one line, idle first', () => {
  assert.equal(describeNodes({ nodes: { ALLOCATED: 4, IDLE: 2, DOWN: 1 } }), '2 idle · 4 allocated · 1 down')
  assert.equal(describeNodes(null), '')
})

test('the job is known by name at submission, by id once it runs', () => {
  const lines = ['[2mSubmitting SLURM job qibocal-nb-a1b2c3 on partition gpu; waiting for a compute node.[0m']
  assert.equal(jobNameFromLog(lines), 'qibocal-nb-a1b2c3')
  assert.equal(jobNameFromLog(['Submitting SLURM job on partition gpu']), null, 'a job the caller named is not ours to find')
  const jobs = [
    { id: '7', name: 'other', user: 'me', state: 'PENDING' },
    { id: '9', name: 'qibocal-nb-a1b2c3', user: 'me', state: 'PENDING' }
  ]
  assert.equal(positionOf(jobs, null, 'qibocal-nb-a1b2c3'), 2)
  assert.deepEqual(filterJobs(jobs, { jobName: 'qibocal-nb-a1b2c3' }).map(job => job.id), ['9', '7'])
  assert.equal(isOwnJob(jobs[1], { jobId: '7', jobName: 'qibocal-nb-a1b2c3' }), false, 'the id, once known, rules')
})

test('the recap says who is busy and what is mine', () => {
  const data = { user: 'me', jobs: [{ id: '1', user: 'me' }, { id: '2', user: 'ann' }] }
  assert.deepEqual(ownJobs(data).map(job => job.id), ['1'])
  assert.deepEqual(ownJobs({ jobs: [{ id: '1' }] }), [], 'no user, no "mine"')
  assert.equal(
    describeOccupation({ total_nodes: 8, nodes: { ALLOCATED: 5, MIXED: 1, IDLE: 1, DOWN: 1 }, jobs: { RUNNING: 6, PENDING: 3 } }),
    '6 of 8 nodes busy, 1 free, 1 down · 6 running, 3 pending'
  )
  assert.equal(describeOccupation(null), '')
})
