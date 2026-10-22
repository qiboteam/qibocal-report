/**
 * Machines: the SSH destinations the application names, once, in
 * `machines.json` — `{ name: { ssh } }` — for every page to offer and to
 * group by. Connection files keep storing the destination itself, which
 * the command line, qibocal-widgets and qibocal-agent read without the
 * application: a connection is on a machine when its destination is the
 * machine's.
 *
 * Pure, and covered by `tests/machines.test.js`.
 */

/** What a machine is called when it is this one: no destination. */
export const THIS_MACHINE = 'This machine'

const trim = value => String(value || '').trim()

/** The machines, by name: `[{ name, ssh }]`. */
export function machineList(machines = {}) {
  return Object.entries(machines || {})
    .map(([name, entry]) => ({ name, ssh: trim(entry?.ssh) }))
    .filter(machine => machine.ssh)
    .sort((a, b) => a.name.localeCompare(b.name))
}

/** Why a name cannot be a new machine's, or '' when it can. */
export function machineNameError(name, machines = {}) {
  const clean = trim(name)
  if (!clean) return ''
  if (clean !== name || clean.includes('/') || clean.length > 64) return 'A name without surrounding spaces or "/", of at most 64 characters.'
  return Object.hasOwn(machines || {}, clean) ? `${clean} is a machine already.` : ''
}

/** The machines with one added, or its destination changed. */
export function withMachine(machines = {}, name, ssh) {
  return { ...(machines || {}), [name]: { ...(machines?.[name] || {}), ssh: trim(ssh) } }
}

/** The machines without one. */
export function withoutMachine(machines = {}, name) {
  const next = { ...(machines || {}) }
  delete next[name]
  return next
}

/** The machine of a destination, or null: none registered with it, or no destination at all. */
export function machineFor(ssh, list = []) {
  const clean = trim(ssh)
  return clean ? list.find(machine => machine.ssh === clean) || null : null
}

/** How a destination is shown: its machine's name, the destination itself, or this machine. */
export function machineLabel(ssh, list = []) {
  const clean = trim(ssh)
  return clean ? machineFor(clean, list)?.name || clean : THIS_MACHINE
}

/**
 * Every use of a destination across the application: `[{ kind, name, ssh }]`
 * — a notebook session, a remote execution connection, an agent
 * configuration of this machine, one kept for a machine (`host`), or a
 * server started on another machine, by its remembered launch.
 */
export function destinationUses({ notebooks = {}, remotes = {}, agents = {}, hosts = {}, launches = {}, servers = [] } = {}) {
  const uses = []
  for (const [name, options] of Object.entries(notebooks || {})) uses.push({ kind: 'notebook', name, ssh: trim(options?.ssh) })
  for (const [name, options] of Object.entries(remotes || {})) uses.push({ kind: 'remote', name, ssh: trim(options?.ssh) })
  for (const [name, entry] of Object.entries(agents?.agents || {})) uses.push({ kind: 'agent', name, ssh: trim(entry?.ssh) })
  for (const [host, kept] of Object.entries(hosts || {})) {
    for (const [name, entry] of Object.entries(kept?.agents || {})) uses.push({ kind: 'kept', name, host, ssh: trim(entry?.ssh) })
  }
  for (const [url, options] of Object.entries(launches || {})) {
    if (!trim(options?.ssh)) continue
    const server = servers.find(entry => trim(entry.url).replace(/\/+$/, '') === url.replace(/\/+$/, ''))
    uses.push({ kind: 'server', name: server?.name || url, url, ssh: trim(options.ssh) })
  }
  return uses
}

/** What uses a machine: what reaches its destination, and the agent configurations kept for it. */
export function usesOf(machine, uses = []) {
  return uses.filter(use => (use.ssh && use.ssh === machine.ssh) || (use.kind === 'kept' && use.host === machine.name))
}

/** The destinations in use that no machine names yet, each once. */
export function unnamedDestinations(uses = [], list = []) {
  return [...new Set(uses.map(use => use.ssh).filter(ssh => ssh && !machineFor(ssh, list)))].sort()
}

/** A map of connections — `notebooks.json`, `remotes.json`'s — with a destination moved. */
export function retargetConnections(connections = {}, from, to) {
  return Object.fromEntries(Object.entries(connections || {}).map(([name, options]) =>
    [name, trim(options?.ssh) === from ? { ...options, ssh: to } : options]))
}

/** agents.json, with a destination moved in its configurations. */
export function retargetAgents(document = {}, from, to) {
  if (!document?.agents) return document
  return { ...document, agents: retargetConnections(document.agents, from, to) }
}

/** The configurations kept for machines, with a destination moved in them. */
export function retargetHosts(hosts = {}, from, to) {
  return Object.fromEntries(Object.entries(hosts || {}).map(([host, kept]) =>
    [host, { ...kept, agents: retargetConnections(kept?.agents || {}, from, to) }]))
}

/** The remembered server launches, with a destination moved. */
export function retargetLaunches(launches = {}, from, to) {
  return retargetConnections(launches, from, to)
}

/**
 * The remotes of the Agents page, before there were machines — keys of
 * `agent-hosts.json` with their destination — moved into the machines once:
 * each becomes a machine of the same name, unless one is already called
 * so, and `agent-hosts.json` keeps only the configurations kept for each.
 */
export function migrateAgentRemotes(machines = {}, hosts = {}) {
  let next = { ...(machines || {}) }
  const kept = {}
  let changed = false
  for (const [name, entry] of Object.entries(hosts || {})) {
    const { ssh, ...rest } = entry || {}
    if (ssh !== undefined || !Object.hasOwn(next, name)) {
      if (!Object.hasOwn(next, name)) next = withMachine(next, name, trim(ssh) || name)
      changed = true
    }
    kept[name] = { ...rest, agents: rest.agents || {} }
  }
  return { machines: next, hosts: kept, changed }
}

/**
 * The machines a list can be filtered by, from the destinations its
 * entries use: `[{ value, label }]` — all of them, this machine when some
 * reach no other, then each machine, named or by its destination.
 */
export function machineOptions(destinations = [], list = []) {
  const labels = new Set()
  let local = false
  for (const ssh of destinations) {
    if (trim(ssh)) labels.add(machineLabel(ssh, list))
    else local = true
  }
  return [
    { value: 'all', label: 'All' },
    ...(local ? [{ value: 'local', label: THIS_MACHINE }] : []),
    ...[...labels].sort().map(label => ({ value: label, label }))
  ]
}

/** Whether a destination is on the machine a filter chose: `all`, `local`, or a machine's label. */
export function onMachine(ssh, value = 'all', list = []) {
  if (value === 'all') return true
  if (value === 'local') return !trim(ssh)
  return Boolean(trim(ssh)) && machineLabel(ssh, list) === value
}
