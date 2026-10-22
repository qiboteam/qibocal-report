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

/**
 * The name the worker gave the job, from the "Submitting SLURM job …" line
 * the command line prints at submission: in the queue at once, where the
 * id arrives only once a compute node has started.
 */
export function jobNameFromLog(lines = []) {
  for (const line of lines) {
    const match = /Submitting SLURM job (qibocal-nb-[0-9a-f]+)/.exec(stripAnsi(line))
    if (match) return match[1]
  }
  return null
}

/** Whether a job of the queue is this session's: by id when known, by name until then. */
export function isOwnJob(job, { jobId = null, jobName = null } = {}) {
  if (jobId) return job.id === jobId
  return Boolean(jobName) && job.name === jobName
}

export function stripAnsi(text) {
  return String(text ?? '').replace(/\[[0-9;]*[A-Za-z]/g, '')
}

/** The jobs to show: mine, in these states, matching this text; ours first. */
export function filterJobs(jobs = [], { mine = false, user = null, states = [], search = '', jobId = null, jobName = null } = {}) {
  const wanted = new Set(states.map(state => state.toUpperCase()))
  const needle = search.trim().toLowerCase()
  return jobs
    .filter(job => !mine || !user || job.user === user)
    .filter(job => !wanted.size || wanted.has(String(job.state || '').toUpperCase().split(' ')[0]))
    .filter(job => !needle || [job.id, job.name, job.user, job.nodes, job.reason, job.partition]
      .some(value => String(value || '').toLowerCase().includes(needle)))
    .sort((left, right) => {
      const own = { jobId, jobName }
      return Number(isOwnJob(right, own)) - Number(isOwnJob(left, own))
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
export function positionOf(jobs = [], jobId, jobName = null) {
  if (!jobId && !jobName) return null
  const pending = jobs.filter(job => String(job.state || '').toUpperCase().startsWith('PENDING'))
  const index = pending.findIndex(job => isOwnJob(job, { jobId, jobName }))
  return index < 0 ? null : index + 1
}

/** The jobs of the user the queue was asked as, for the home page's recap. */
export function ownJobs(data) {
  if (!data?.user) return []
  return (data.jobs || []).filter(job => job.user === data.user)
}

/** The occupation of a queue in a few words: busy and free nodes, running and pending jobs. */
export function describeOccupation(summary) {
  if (!summary) return ''
  const nodes = summary.nodes || {}
  const busy = (nodes.ALLOCATED || 0) + (nodes.MIXED || 0) + (nodes.COMPLETING || 0)
  const free = nodes.IDLE || 0
  const down = (nodes.DOWN || 0) + (nodes.DRAINED || 0) + (nodes.DRAINING || 0)
  const parts = []
  if (summary.total_nodes) {
    parts.push(`${busy} of ${summary.total_nodes} nodes busy, ${free} free${down ? `, ${down} down` : ''}`)
  }
  const jobs = summary.jobs || {}
  parts.push(`${jobs.RUNNING || 0} running, ${jobs.PENDING || 0} pending`)
  return parts.join(' · ')
}

/** One key per machine: its SSH destination, or this one. */
export function machineKey(ssh) {
  return String(ssh || '').trim() || 'local'
}

/**
 * The queues grouped by the machine they are on, for the tree of Queues:
 * `[{ key, ssh, label, partitions: [{ key, queue }] }]`. A machine is
 * named as the application's machine of the same destination is, when there is one;
 * this one comes last.
 */
export function groupMachines(queues = [], remotes = []) {
  const machines = new Map()
  for (const queue of queues) {
    const key = machineKey(queue.ssh)
    if (!machines.has(key)) {
      const remote = queue.ssh ? remotes.find(entry => entry.ssh === queue.ssh) : null
      machines.set(key, { key, ssh: queue.ssh || null, label: queue.ssh ? remote?.name || queue.ssh : 'This machine', partitions: [] })
    }
    const partitions = machines.get(key).partitions
    if (!partitions.some(entry => entry.queue.partition === queue.partition)) partitions.push({ key: queueKey(queue), queue })
  }
  return [...machines.values()].sort((a, b) => (a.ssh === null) - (b.ssh === null) || a.label.localeCompare(b.label))
}

/** A partition's queue out of its machine's answer, as one queue alone is answered. */
export function partitionAnswer(machine, partition) {
  const own = machine?.queues?.[partition]
  if (!machine || !own) return null
  return {
    ssh: machine.ssh,
    partition,
    user: machine.user,
    jobs: own.jobs,
    nodes: own.nodes,
    summary: own.summary,
    fetched_at: machine.fetched_at,
    error: machine.error,
    stderr: machine.stderr
  }
}
