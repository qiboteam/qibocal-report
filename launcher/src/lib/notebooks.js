/**
 * Notebook connection options, described once for the whole interface.
 *
 * The shape mirrors `qibocal_report.notebook.NotebookOptions`, so a connection
 * saved here is understood verbatim by `qibocal notebook connect`.
 */
export const NOTEBOOK_FIELDS = [
  {
    name: 'ssh',
    label: 'SSH destination',
    type: 'text',
    placeholder: 'user@login-node',
    help: 'SSH options followed by a host or user@host. Leave empty to run locally.'
  },
  {
    name: 'queue',
    label: 'SLURM partition',
    type: 'text',
    placeholder: 'mychip',
    help: 'Submit the session to this partition on the access node.'
  },
  {
    name: 'slurm',
    label: 'Extra srun options',
    type: 'text',
    placeholder: '--time 02:00:00 --mem 8G',
    help: 'Passed verbatim to srun when a partition is selected.'
  },
  {
    name: 'workdir',
    label: 'Working directory',
    type: 'text',
    placeholder: '/shared/calibration',
    help: 'Directory the notebook starts from on the access node.'
  },
  {
    name: 'venv',
    label: 'Kernel environment',
    type: 'text',
    placeholder: 'qibocal',
    default: 'qibocal',
    help: 'Environment name or path on the computing node.'
  },
  {
    name: 'subnet',
    label: 'Computing node subnet',
    type: 'text',
    placeholder: '192.168.0.0/24',
    help: 'Restrict SLURM computing-node addresses to this network.'
  },
  {
    name: 'marimo',
    label: 'Interface',
    type: 'choice',
    default: false,
    options: [
      { value: false, label: 'JupyterLab' },
      { value: true, label: 'Marimo' }
    ]
  },
  {
    name: 'timeout',
    label: 'Startup timeout',
    type: 'number',
    default: 300,
    unit: 'seconds',
    help: 'How long to wait for the session and its tunnels to answer.'
  }
]

export function defaultNotebookOptions() {
  return Object.fromEntries(
    NOTEBOOK_FIELDS.map(field => [field.name, field.default ?? (field.type === 'number' ? null : '')])
  )
}

/** Fill the editor with a stored connection, keeping unset options at their default. */
export function toEditorValues(connection = {}) {
  const values = defaultNotebookOptions()
  for (const field of NOTEBOOK_FIELDS) {
    const stored = connection?.[field.name]
    if (stored === undefined || stored === null) continue
    values[field.name] = field.type === 'choice' ? Boolean(stored) : stored
  }
  return values
}

function validSubnet(value) {
  const [address, prefix, ...rest] = value.split('/')
  if (rest.length || prefix === undefined || !/^\d{1,3}$/.test(prefix)) return false
  const length = Number(prefix)
  if (address.includes(':')) {
    return length <= 128 && /^[0-9a-fA-F:]+$/.test(address) && address.length > 1
  }
  const octets = address.split('.')
  if (octets.length !== 4 || length > 32) return false
  if (!octets.every(octet => /^\d{1,3}$/.test(octet) && Number(octet) <= 255)) return false
  // Python's ip_network rejects networks whose host bits are set.
  const bits = octets.reduce((total, octet) => total * 256 + Number(octet), 0)
  return (bits % 2 ** (32 - length)) === 0
}

/**
 * Keep only the options that differ from the defaults, validating the ones
 * the command line would otherwise reject with a cryptic message.
 */
export function normalizeNotebookOptions(values = {}) {
  const options = {}
  const errors = {}

  for (const field of NOTEBOOK_FIELDS) {
    const raw = values[field.name]
    if (field.type === 'choice') {
      if (Boolean(raw) !== Boolean(field.default)) options[field.name] = Boolean(raw)
      continue
    }
    if (field.type === 'number') {
      if (raw === '' || raw === null || raw === undefined) continue
      const parsed = Number(raw)
      if (!Number.isFinite(parsed) || parsed <= 0) {
        errors[field.name] = 'Enter a positive number of seconds.'
        continue
      }
      if (parsed !== field.default) options[field.name] = parsed
      continue
    }
    const text = typeof raw === 'string' ? raw.trim() : ''
    if (!text || text === field.default) continue
    if (field.name === 'subnet' && !validSubnet(text)) {
      errors.subnet = 'Enter a network such as 192.168.0.0/24.'
      continue
    }
    options[field.name] = text
  }

  const warnings = {}
  if (options.queue === undefined && options.slurm) {
    warnings.slurm = 'Extra srun options only apply once a SLURM partition is selected.'
  }

  return { options, errors, warnings, valid: Object.keys(errors).length === 0 }
}

/** One-line summary of a stored connection, for the connection list. */
export function describeConnection(connection = {}) {
  const parts = []
  if (connection.ssh) parts.push(`ssh ${connection.ssh}`)
  else parts.push('local session')
  if (connection.queue) parts.push(`partition ${connection.queue}`)
  if (connection.workdir) parts.push(connection.workdir)
  parts.push(connection.marimo ? 'Marimo' : 'JupyterLab')
  return parts.join(' · ')
}
