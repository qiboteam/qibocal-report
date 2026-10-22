/**
 * Agent configurations: qibocal-agent's, from qibocal-mcp-servers. Those for
 * this machine are its `agents.json` — every configuration under `agents`,
 * `default` the one used without a name — read and written as the tool
 * expects it: its file, strictly validated, so no key of ours goes in it.
 * Those for another machine — an assistant on an access node — are kept
 * here, under the SSH remote they are pushed to.
 *
 * SSH remotes are named here, apart from the configurations: several
 * configurations reach the same access node, and an assistant there keeps
 * its own. They are the keys of `agent-hosts.json`, each with its `ssh`
 * destination — the key itself when it has none — and the configurations
 * kept for it; agents.json itself only ever holds the destination.
 *
 * Pure, and covered by `tests/agents.test.js`.
 */

/** A name qibocal-agent accepts: a letter or digit, then letters, digits, underscores, hyphens. */
export const AGENT_NAME = /^[A-Za-z0-9][A-Za-z0-9_-]*$/
/** Names qibocal-agent reserves. */
export const RESERVED_AGENT_NAMES = ['agent', 'agents']
/** The configuration used when none is named. */
export const DEFAULT_AGENT = 'default'

/** Why a name cannot be a configuration's, or '' when it can. */
export function agentNameError(name) {
  if (!name) return 'A configuration needs a name: default is the one used without one.'
  if (!AGENT_NAME.test(name)) return 'A letter or digit, then letters, digits, underscores or hyphens.'
  if (RESERVED_AGENT_NAMES.includes(name)) return `${name} is reserved by qibocal-agent.`
  return ''
}

/** The settings, as the configuration guide lists them; `list` ones are one value per line. */
export const AGENT_FIELDS = [
  { name: 'platform', label: 'Platform', type: 'text', placeholder: 'qw5q_platinum', help: 'Required at run time.', info: 'The installed Qibolab platform the calibration runs on.' },
  { name: 'model', label: 'Model', type: 'text', placeholder: 'openai:gpt-4.1', help: 'For autonomous runs.', info: 'A vision-capable Pydantic AI model identifier, github-copilot:MODEL_ID or openwebui:MODEL_ID. Its credentials stay in the environment: the launcher stores no key.' },
  { name: 'ssh', label: 'SSH destination', type: 'text', placeholder: 'access-node', help: 'Where the calibration server starts. Empty: where the agent runs.', info: 'The machine the calibration server is started on, over SSH, from wherever the configuration is used: usually a cluster\'s access node. One of the remotes, or any destination ssh takes. Empty, the server starts where the agent or the assistant runs, which must then reach the instruments itself.' },
  { name: 'partition', label: 'SLURM partition', type: 'text', help: 'Empty: operations run where the server is.', info: 'From the machine the server starts on, each operation is one srun job on this partition, whose nodes reach the instruments; nothing is allocated between operations. Empty, the server runs them itself, so it must reach the instruments.' },
  { name: 'objective', label: 'Objective', type: 'textarea', placeholder: 'Calibrate qubit 0\'s drive frequency… Sweep no wider than 20 MHz… Stop on errors.', help: 'The objective of a run given none.', info: 'The calibration goal, with operator-approved hardware limits, an execution budget and stopping criteria. A run\'s own prompt overrides it.' },
  { name: 'model_base_url', label: 'Model endpoint', type: 'text', advanced: true, help: 'For openwebui: and github-copilot: models.', info: 'OpenWebUI URLs include /api. No credentials in URLs.' },
  { name: 'output', label: 'Output', type: 'text', advanced: true, help: 'Default: the name, under ~/.local/share/qibocal/agents/runs.', info: 'Where the reports are written, on the execution host. Reports serves it.' },
  { name: 'workdir', label: 'Working directory', type: 'text', advanced: true, help: 'Default: the name, under ~/.cache/qibocal/agents/work.' },
  { name: 'platforms_dir', label: 'Platforms folder', type: 'text', advanced: true, help: 'QIBOLAB_PLATFORMS on the execution host.' },
  { name: 'venv', label: 'Environment', type: 'text', advanced: true, help: 'Default: the name, under ~/.cache/qibocal/agents/envs.', info: 'The managed environment on the execution host. Not together with a server interpreter.' },
  { name: 'server_python', label: 'Server interpreter', type: 'text', advanced: true, help: 'An interpreter that already holds the server.' },
  { name: 'dependency', label: 'Dependencies', type: 'list', advanced: true, placeholder: 'qibolab-qblox==0.0.4', help: 'One requirement per line.' },
  { name: 'platform_repo', label: 'Platform repositories', type: 'list', advanced: true, help: 'One trusted repository per line, in lookup order.' },
  { name: 'slurm_arg', label: 'srun options', type: 'list', advanced: true, placeholder: '--time=00:15:00', help: 'One option per line; needs a partition.' },
  { name: 'timeout', label: 'Timeout', type: 'number', advanced: true, unit: 'seconds', help: 'Default: 3600, per operation, queue included.' }
]

const KNOWN = new Set(AGENT_FIELDS.map(field => field.name))

/** The editor values of a stored entry: lists one value per line, everything else as it is. */
export function agentEditorValues(entry = {}) {
  const values = {}
  for (const field of AGENT_FIELDS) {
    const stored = entry?.[field.name]
    if (field.type === 'list') values[field.name] = Array.isArray(stored) ? stored.join('\n') : ''
    else if (field.type === 'number') values[field.name] = stored ?? null
    else values[field.name] = typeof stored === 'string' ? stored : ''
  }
  return values
}

/**
 * The entry an editor describes, as qibocal-agent validates it: nonempty
 * strings, lists of nonempty strings, a positive timeout, no null. Keys the
 * editor does not know — a `report` section, say — are kept from the stored
 * entry.
 */
export function agentEntry(values = {}, { previous = {} } = {}) {
  const entry = {}
  const errors = {}
  for (const [key, value] of Object.entries(previous || {})) {
    if (!KNOWN.has(key)) entry[key] = value
  }
  for (const field of AGENT_FIELDS) {
    const raw = values[field.name]
    if (field.type === 'list') {
      const items = String(raw || '').split('\n').map(item => item.trim()).filter(Boolean)
      if (items.length) entry[field.name] = items
    } else if (field.type === 'number') {
      if (raw === '' || raw === null || raw === undefined) continue
      const number = Number(raw)
      if (!Number.isFinite(number) || number <= 0) errors[field.name] = 'Enter a positive number of seconds.'
      else entry[field.name] = number
    } else {
      const text = String(raw || '').trim()
      if (text) entry[field.name] = text
    }
  }
  if (entry.venv && entry.server_python) errors.server_python = 'Either an environment or a server interpreter, not both.'
  if (entry.slurm_arg?.length && !entry.partition) errors.slurm_arg = 'srun options need a partition.'
  return { entry, errors, valid: Object.keys(errors).length === 0 }
}

/**
 * Every configuration, as the page lists them: `{ key, name, host, entry }`
 * — `host` 'local' for this machine's agents.json, or the remote one is kept
 * for, with `destination`, where it is pushed.
 */
export function agentConfigurations(document = {}, hosts = {}) {
  const list = []
  for (const [name, entry] of Object.entries(document?.agents || {})) list.push({ key: `local:${name}`, name, host: 'local', entry })
  for (const [host, kept] of Object.entries(hosts || {})) {
    const destination = remoteDestination(host, kept)
    for (const [name, entry] of Object.entries(kept?.agents || {})) list.push({ key: `${host}:${name}`, name, host, destination, entry })
  }
  return list
}

/** Where a remote is reached: its `ssh`, or its name, as the remotes kept before destinations were. */
function remoteDestination(name, kept) {
  const ssh = typeof kept?.ssh === 'string' ? kept.ssh.trim() : ''
  return ssh || name
}

/** The SSH remotes, by name: `{ name, ssh, kept }`, `kept` counting the configurations kept for each. */
export function agentRemotes(hosts = {}) {
  return Object.entries(hosts || {})
    .map(([name, kept]) => ({ name, ssh: remoteDestination(name, kept), kept: Object.keys(kept?.agents || {}).length }))
    .sort((a, b) => a.name.localeCompare(b.name))
}

/** The remotes with one added, or its destination changed; its configurations stay. */
export function withRemote(hosts = {}, name, ssh) {
  const next = JSON.parse(JSON.stringify(hosts || {}))
  next[name] = { ...(next[name] || {}), ssh: ssh.trim(), agents: next[name]?.agents || {} }
  return next
}

/** The remotes without one: only one that keeps no configuration goes. */
export function withoutRemote(hosts = {}, name) {
  if (Object.keys(hosts?.[name]?.agents || {}).length) throw new Error(`${name} still keeps configurations: move or remove them first.`)
  const next = JSON.parse(JSON.stringify(hosts || {}))
  delete next[name]
  return next
}

/**
 * The remote a configuration reaches its hardware through: the registered
 * one with its SSH destination, the destination itself when none is
 * registered, or null — reached directly from where it runs.
 */
export function reachedRemote(entry = {}, remotes = []) {
  const ssh = String(entry?.ssh || '').trim()
  if (!ssh) return null
  return remotes.find(remote => remote.ssh === ssh)?.name || ssh
}

/**
 * Whether a configuration passes the page's filters, together: where it is
 * kept (`all`, `local`, or a remote) and what it reaches (`all`, `direct`,
 * or a remote).
 */
export function agentShown(item, { kept = 'all', reaches = 'all' } = {}, remotes = []) {
  if (kept !== 'all' && item.host !== kept) return false
  if (reaches === 'all') return true
  const reached = reachedRemote(item.entry, remotes)
  return reaches === 'direct' ? reached === null : reached === reaches
}

/** The agents.json with one configuration of this machine set — or removed, with a null entry. */
export function withLocalAgent(document = {}, name, entry) {
  const next = JSON.parse(JSON.stringify(document || {}))
  const agents = { ...(next.agents || {}) }
  if (entry) agents[name] = entry
  else delete agents[name]
  if (Object.keys(agents).length) next.agents = agents
  else delete next.agents
  return next
}

/** The kept configurations with one set — or removed — for a remote, which stays either way. */
export function withHostAgent(hosts = {}, host, name, entry) {
  const next = JSON.parse(JSON.stringify(hosts || {}))
  const kept = next[host] || { ssh: host, agents: {} }
  kept.agents = { ...(kept.agents || {}) }
  if (entry) kept.agents[name] = entry
  else delete kept.agents[name]
  next[host] = kept
  return next
}

/** Where a configuration's reports are, on its execution host: its output, or the default under the data home. */
export function agentReports(entry = {}, name = DEFAULT_AGENT) {
  const output = String(entry?.output || '').trim()
  if (output.startsWith('/') || output.startsWith('~')) return output
  return `~/.local/share/qibocal/agents/runs/${output || name || DEFAULT_AGENT}`
}

/**
 * The registration of `qibocal-agent mcp` in an assistant: one for every
 * configuration, since it starts none until the assistant selects one.
 * `executable` is the absolute path of qibocal-agent, so an assistant
 * started anywhere runs it in its own environment.
 */
export function mcpSnippet(executable = '') {
  const command = String(executable || '').trim() || 'qibocal-agent'
  return JSON.stringify({ mcpServers: { qibocal: { command, args: ['mcp'], timeout: 3600000 } } }, null, 2)
}

/** One-line summary of a configuration. */
export function describeAgent(entry = {}) {
  const parts = [entry.platform ? `platform ${entry.platform}` : 'no platform']
  if (entry.ssh) parts.push(`ssh ${entry.ssh}`)
  if (entry.partition) parts.push(`partition ${entry.partition}`)
  if (entry.model) parts.push(entry.model)
  return parts.join(' · ')
}
