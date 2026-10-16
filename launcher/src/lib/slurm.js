/**
 * The SLURM queue, as the launcher looks at it: pure helpers, covered by
 * `tests/slurm.test.js`. The queries themselves go through the command
 * line; here is what identifies a queue, how a session's own job is found
 * in its log, and how the jobs are filtered for the panel.
 */

/** The queue a set of notebook options points at, or null for a session without one. */
export function queueOf(options) {
  const partition = String(options?.queue || '').trim()
  if (!partition) return null
  return { ssh: String(options?.ssh || '').trim() || null, partition }
}

/** One key per queue: the same partition on the same host is one queue, however it is reached. */
export function queueKey(queue) {
  if (!queue) return null
  return `${queue.ssh || 'local'}|${queue.partition}`
}

/** The job the worker said it got, from the lines the command line printed. */
export function jobIdFromLog(lines = []) {
  for (const line of lines) {
    const match = /SLURM_JOB_ID\s+(\d+)/.exec(stripAnsi(line))
    if (match) return match[1]
  }
  return null
}

export function stripAnsi(text) {
  return String(text ?? '').replace(/\[[0-9;]*[A-Za-z]/g, '')
}

/** The jobs to show: mine, in these states, matching this text; ours first. */
export function filterJobs(jobs = [], { mine = false, user = null, states = [], search = '', jobId = null } = {}) {
  const wanted = new Set(states.map(state => state.toUpperCase()))
  const needle = search.trim().toLowerCase()
  return jobs
    .filter(job => !mine || !user || job.user === user)
    .filter(job => !wanted.size || wanted.has(String(job.state || '').toUpperCase().split(' ')[0]))
    .filter(job => !needle || [job.id, job.name, job.user, job.nodes, job.reason, job.partition]
      .some(value => String(value || '').toLowerCase().includes(needle)))
    .sort((left, right) => {
      const ours = Number(right.id === jobId) - Number(left.id === jobId)
      return ours || 0
    })
}

/** The states worth a filter chip, in the order they matter. */
export const JOB_STATES = ['RUNNING', 'PENDING', 'COMPLETING', 'SUSPENDED']

/** How a node state reads: the counts in one line, idle first. */
export function describeNodes(summary) {
  const nodes = summary?.nodes || {}
  const order = ['IDLE', 'MIXED', 'ALLOCATED', 'COMPLETING', 'DOWN', 'DRAINED', 'DRAINING', 'RESERVED', 'MAINT']
  const parts = order
    .filter(state => nodes[state])
    .map(state => `${nodes[state]} ${state.toLowerCase()}`)
  for (const [state, count] of Object.entries(nodes)) {
    if (!order.includes(state) && count) parts.push(`${count} ${state.toLowerCase()}`)
  }
  return parts.join(' · ')
}

/** Where our job stands among the pending ones of its partition: 1 for first in line. */
export function positionOf(jobs = [], jobId) {
  if (!jobId) return null
  const pending = jobs.filter(job => String(job.state || '').toUpperCase().startsWith('PENDING'))
  const index = pending.findIndex(job => job.id === jobId)
  return index < 0 ? null : index + 1
}
