/**
 * Notebook connection options, described once for the whole interface.
 *
 * The shape mirrors `qibocamp.remote.notebook.NotebookOptions`, so a connection
 * saved here is understood verbatim by `qibocamp notebook connect`.
 */
export const NOTEBOOK_FIELDS = [
  {
    name: 'ssh',
    places: ['access', 'compute'],
    label: 'SSH destination',
    type: 'text',
    placeholder: 'user@host',
    help: 'Empty: a local session.',
    info: 'SSH options followed by a host or user@host, the way ssh takes them. Host aliases, agent authentication and jump hosts from the SSH configuration all work; the destination comes last.'
  },
  {
    name: 'queue',
    places: ['compute'],
    label: 'SLURM partition',
    type: 'text',
    help: 'Empty: no SLURM, the session runs on the access node.',
    info: 'Submit the session to this partition with srun: the notebook then runs on a computing node, reached through a second tunnel from the access node.'
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
    name: 'slurm',
    places: ['compute'],
    label: 'Extra srun options',
    type: 'text',
    advanced: true,
    placeholder: '--time 02:00:00 --mem 8G',
    help: 'Passed to srun verbatim.',
    info: 'Only once a partition is selected; time limits, memory and GPUs go here, as srun takes them.'
  },
  {
    name: 'workdir',
    label: 'Working directory',
    type: 'text',
    advanced: true,
    help: 'Default: where the login lands.',
    info: 'Directory the notebook starts from on the access node, which is also the root of its file browser.'
  },
  {
    name: 'venv',
    label: 'Kernel environment',
    type: 'text',
    advanced: true,
    placeholder: 'qibocal',
    placeholderFor: values => (values?.name ? environmentName(values.name) : 'qibocal'),
    help: 'Default: the connection\'s name, or qibocal for a session not saved.',
    info: 'An environment name, resolved under ~/.cache/qibocamp/envs on the computing node, or an absolute path there. Created, with the notebook and a kernel, when missing.'
  },
  {
    name: 'subnet',
    places: ['compute'],
    label: 'Computing node subnet',
    type: 'text',
    advanced: true,
    placeholder: '192.168.0.0/24',
    help: 'Empty: any address the computing node reports.',
    info: 'A network, in CIDR notation, that the address of the SLURM computing node must belong to. Left empty, the node picks the interface it routes through to reach the access node, leaving out any address the two share, such as a container bridge; set this when the notebook is reported ready but the access node cannot reach it.'
  },
  {
    name: 'remote',
    label: 'Remote execution',
    type: 'select',
    help: 'None: the acquisitions run in the notebook.',
    info: 'A connection of Remote execution, where qibocal-widgets\' Remote plugin runs the notebook\'s acquisitions. The session exports its name as QIBOCAL_WIDGETS_CONNECTION, and writes the connection to remotes.json where the notebook runs, so Remote() finds it with no change to the notebook. Only the connections that make sense from where the session runs are offered.'
  },
  {
    name: 'reports',
    label: 'Reports folder',
    type: 'text',
    advanced: true,
    placeholder: 'reports',
    help: 'Empty: the working directory. Relative to it.',
    info: 'Where the session\'s calibrations keep their reports. It is created when the session starts, and exported to the notebook and its kernels as QIBOCAMP_REPORTS_DIR, for the code there to write to — the working directory, and the files the notebook sees, stay as they are. Reports serves this folder.'
  },
  {
    name: 'requirements',
    label: 'Kernel requirements',
    type: 'textarea',
    advanced: true,
    placeholder: 'numpy>=2\nscipy\nqibolab[qm]',
    help: 'requirements.txt format. Empty: qibocal alone.',
    info: 'What the kernel environment must hold, one requirement per line, as pip reads a requirements.txt file. Installed when the environment is created; when the list changes, the next session installs it on top of the environment, without rebuilding it — nothing is uninstalled.'
  },
  {
    name: 'rebuild_on_compute',
    places: ['compute'],
    label: 'Regenerate env on',
    type: 'choice',
    advanced: true,
    default: false,
    options: [
      { value: false, label: 'Access node' },
      { value: true, label: 'Computing node' }
    ],
    help: 'Only with a SLURM partition.',
    info: 'Where Regenerate env rebuilds the kernel environment of a SLURM session. The access node by default: the environment lives in a home the nodes share, and nothing waits in the queue. A computing node when the environment has to be built there — a different architecture, a local disk — through srun like a session, its queue shown in Running.'
  },
  {
    name: 'timeout',
    label: 'Startup timeout',
    type: 'number',
    advanced: true,
    default: 300,
    unit: 'seconds',
    help: 'Default: 300 seconds.',
    info: 'How long to wait for the session and its tunnels to answer, environment preparation included.'
  }
]

/**
 * Where a session runs, as servers say where they run: here, on the access
 * node SSH reaches, or on a computing node through a SLURM partition from
 * there. Every place keeps the same features — the environment, its
 * requirements, Regenerate env and Reports — and only the fields that make
 * sense there are shown (`places` on a field) and kept.
 */
export const NOTEBOOK_PLACES = [
  { value: 'local', label: 'This machine', help: 'A session here, in an environment of its own: for a direct connection to the instruments.' },
  { value: 'access', label: 'Access node', help: 'A session on the machine SSH reaches, tunnelled back: for offline processing, or setups without queues.' },
  { value: 'compute', label: 'Computing node', help: 'A session on a node of a SLURM partition, reached from the access node.' }
]

/** The place stored options describe: a partition is a computing node, a destination the access node. */
export function placeOf(options = {}) {
  if (String(options?.queue || '').trim()) return 'compute'
  if (String(options?.ssh || '').trim()) return 'access'
  return 'local'
}

/** Whether a field makes sense in a place. */
export function fieldApplies(field, place) {
  return !place || !Array.isArray(field.places) || field.places.includes(place)
}

/**
 * The kernel environment a registered connection uses by default: its name,
 * made safe for a folder — as `qibocamp.remote.notebook.environment_name`.
 */
export function environmentName(connection) {
  // No leading underscore either: _remote holds the remote connections' own.
  const safe = String(connection || '').replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^[-._]+|[-.]+$/g, '')
  return safe || 'qibocal'
}

/**
 * The environment a named remote execution connection uses by default: its
 * name, made safe as a session's, under `_remote/` — apart from the sessions'
 * own, as qibocal-widgets' plugin resolves it.
 */
export function remoteEnvironmentName(connection) {
  return `_remote/${environmentName(connection)}`
}

/** Every field at its default; remote connections pass their own fields. */
export function defaultNotebookOptions(fields = NOTEBOOK_FIELDS) {
  return Object.fromEntries(fields.map(field => [field.name, field.default ?? (field.type === 'number' ? null : '')]))
}

/** A blank editor: every field at its default, here, and no name. */
export function blankEditor(fields = NOTEBOOK_FIELDS) {
  return { ...defaultNotebookOptions(fields), where: 'local', name: '' }
}

/** Fill the editor with a stored connection, keeping unset options at their default. */
export function toEditorValues(connection = {}, fields = NOTEBOOK_FIELDS) {
  const values = defaultNotebookOptions(fields)
  for (const field of fields) {
    const stored = connection?.[field.name]
    if (stored === undefined || stored === null) continue
    values[field.name] = field.type === 'choice' ? Boolean(stored) : stored
  }
  values.where = placeOf(connection)
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
export function normalizeNotebookOptions(values = {}, fields = NOTEBOOK_FIELDS) {
  const options = {}
  const errors = {}
  // The editor's place, when it has one: what does not apply there is left out.
  const place = values.where || null

  for (const field of fields) {
    if (!fieldApplies(field, place)) continue
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
    // A textarea keeps its lines; only the ends are trimmed.
    const text = typeof raw === 'string' ? raw.trim() : ''
    if (!text || text === field.default) continue
    if (field.name === 'subnet' && !validSubnet(text)) {
      errors.subnet = 'Enter a network such as 192.168.0.0/24.'
      continue
    }
    options[field.name] = text
  }

  if (place && place !== 'local' && !options.ssh) errors.ssh = 'Enter the SSH destination of the access node.'
  if (place === 'compute' && !options.queue) errors.queue = 'Enter the SLURM partition the session runs on.'

  const warnings = {}
  if (options.queue === undefined && options.slurm) {
    warnings.slurm = 'Extra srun options only apply once a SLURM partition is selected.'
  }

  return { options, errors, warnings, valid: Object.keys(errors).length === 0 }
}

/**
 * The environment a notebook's report server runs in, on the session's
 * machine: one of its own. The kernel environment holds qibocal and the
 * session's requirements, not necessarily the qibocamp of this launcher.
 */
export const REPORTS_ENVIRONMENT = 'qibocamp'

/** The key a notebook's report server is known by: its connection, or where it runs. */
export function notebookKey(options = {}, name = null) {
  if (name) return name
  const text = value => String(value || '').trim()
  return `${text(options.ssh) || 'local'}|${text(options.workdir) || '~'}`
}

/**
 * The report server of a notebook session: on the same channel — the same
 * SSH destination, its own connection — serving the session's reports
 * folder, relative to where it starts; without one, where it starts: the
 * working directory, or the home folder (`home`, here). Started for a
 * look, as "<session> reports": nothing is registered.
 */
export function reportServerOptions(options = {}, { name = null, home = null, port = 8000 } = {}) {
  const text = value => String(value || '').trim() || null
  const ssh = text(options.ssh)
  const workdir = text(options.workdir)
  const label = name || (ssh ? ssh.split(/\s+/).pop() : 'notebook')
  // Where the session starts, and its reports folder, relative to it.
  const start = workdir || (ssh ? '~' : home)
  const reports = text(options.reports)
  const absolute = reports && (reports.startsWith('/') || reports.startsWith('~'))
  return {
    mode: 'server',
    name: `${label} reports`,
    // For a look: nothing written to servers.json.
    register: false,
    directory: reports ? (absolute ? reports : `${start.replace(/\/+$/, '')}/${reports}`) : start,
    host: 'localhost',
    port,
    auth: false,
    frontendPort: null,
    ssh,
    venv: ssh ? REPORTS_ENVIRONMENT : null,
    workdir: ssh ? workdir : null,
    install: null
  }
}

/**
 * The remote execution connections a session can use, by name: from this
 * machine, any; from another machine, any but those that would reach that
 * very machine over SSH — from there, the one without a destination does.
 */
export function remoteChoices(remotes = {}, values = {}) {
  const place = values.where || placeOf(values)
  const here = String(values.ssh || '').trim()
  return Object.entries(remotes || {})
    .filter(([, entry]) => place === 'local' || !here || String(entry?.ssh || '').trim() !== here)
    .map(([name]) => name)
}

/** How many requirements a requirements.txt text names: blank lines and comments do not count. */
export function requirementCount(text) {
  return String(text || '').split('\n').map(line => line.trim()).filter(line => line && !line.startsWith('#')).length
}

/** One-line summary of a stored connection, for the connection list. */
export function describeConnection(connection = {}) {
  const parts = []
  if (connection.ssh) parts.push(`ssh ${connection.ssh}`)
  else parts.push('local session')
  if (connection.queue) parts.push(`partition ${connection.queue}`)
  if (connection.workdir) parts.push(connection.workdir)
  parts.push(connection.marimo ? 'Marimo' : 'JupyterLab')
  const requirements = requirementCount(connection.requirements)
  if (requirements) parts.push(`${requirements} requirement${requirements === 1 ? '' : 's'}`)
  if (connection.remote) parts.push(`remote ${connection.remote}`)
  return parts.join(' · ')
}
