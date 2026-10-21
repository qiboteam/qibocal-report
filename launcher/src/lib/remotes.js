/**
 * Remote execution connections: where qibocal-widgets' `Remote` plugin runs
 * the acquisitions of a notebook — over SSH, through SLURM — kept in
 * `remotes.json`, next to the other files of the configuration, which the
 * plugin reads (`Remote(connection="lab")`, or the connection named by
 * `QIBOCAL_WIDGETS_CONNECTION`). See qibocal-widgets'
 * `docs/plan/remote-executor.md`.
 *
 * The fields the two have in common mean the same as a notebook
 * connection's, so they are the very same descriptions; the environments
 * are shared too — same place, same installer, same requirements marker —
 * so Regenerate env is `qibocal notebook rebuild` with these options.
 */
import { NOTEBOOK_FIELDS, normalizeNotebookOptions, defaultNotebookOptions, requirementCount, toEditorValues } from './notebooks.js'

const shared = name => NOTEBOOK_FIELDS.find(field => field.name === name)

export const REMOTE_FIELDS = [
  {
    ...shared('ssh'),
    help: 'Empty: this machine.',
    info: 'SSH options followed by a host or user@host, the way ssh takes them: the access node the acquisitions are dispatched from. Empty, they run on the machine of the notebook.'
  },
  {
    ...shared('queue'),
    help: 'Empty: no SLURM, the acquisition runs on the access node.',
    info: 'Each acquisition is one blocking srun job on this partition, from the access node.'
  },
  {
    name: 'platform',
    label: 'Platform',
    type: 'text',
    placeholder: 'qw11q',
    help: 'Empty: the one the notebook\'s executor names.',
    info: 'The Qibolab platform the jobs create, by name, on the remote side; its parameters and calibration travel with each job.'
  },
  { ...shared('slurm'), info: 'Only once a partition is selected; time limits, memory and GPUs go here, as srun takes them.' },
  { ...shared('workdir'), info: 'Directory the jobs start from on the access node.' },
  {
    ...shared('venv'),
    // A connection names its environment, qibocal unless set: none is derived from its name.
    default: 'qibocal',
    placeholderFor: undefined,
    help: 'Default: qibocal',
    label: 'Environment',
    info: 'An environment name, resolved under ~/.cache/qibocal/envs on the remote side, or an absolute path there — the same place notebook sessions use, so an environment prepared by one is recognised by the other.'
  },
  {
    name: 'python',
    label: 'Python',
    type: 'text',
    advanced: true,
    placeholder: '3.12',
    help: 'Empty: the system python3.',
    info: 'The interpreter of the environment, or a version uv provides it in.'
  },
  shared('requirements'),
  shared('rebuild_on_compute'),
  {
    ...shared('reports'),
    help: 'Empty: the working directory. Relative to it.',
    info: 'Where the executor keeps the outputs of the remote runs, on the access node. Reports serves this folder, on the same channel, in the dashboard.'
  },
  {
    name: 'timeout',
    label: 'Timeout',
    type: 'number',
    advanced: true,
    default: null,
    unit: 'seconds',
    help: 'Empty: the plugin\'s default.',
    info: 'How long a step may take, queue included.'
  }
].filter(Boolean)

export const defaultRemoteOptions = () => defaultNotebookOptions(REMOTE_FIELDS)
export const toRemoteEditorValues = connection => toEditorValues(connection, REMOTE_FIELDS)
export const normalizeRemoteOptions = values => normalizeNotebookOptions(values, REMOTE_FIELDS)

/** One-line summary of a remote connection, for its card. */
export function describeRemote(connection = {}) {
  const parts = [connection.ssh ? `ssh ${connection.ssh}` : 'this machine']
  if (connection.queue) parts.push(`partition ${connection.queue}`)
  if (connection.platform) parts.push(`platform ${connection.platform}`)
  parts.push(connection.venv || 'qibocal')
  const requirements = requirementCount(connection.requirements)
  if (requirements) parts.push(`${requirements} requirement${requirements === 1 ? '' : 's'}`)
  return parts.join(' · ')
}

/** The options of `qibocal notebook rebuild` that regenerate a remote connection's environment. */
export function rebuildOptions(connection = {}) {
  const keep = ['ssh', 'queue', 'slurm', 'workdir', 'venv', 'requirements', 'rebuild_on_compute', 'timeout']
  return Object.fromEntries(keep.filter(key => connection[key] !== undefined && connection[key] !== null && connection[key] !== '').map(key => [key, connection[key]]))
}
