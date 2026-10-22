import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  AGENT_NAME,
  agentConfigurations,
  agentEditorValues,
  agentEntry,
  agentNameError,
  agentReports,
  describeAgent,
  agentRemotes,
  agentShown,
  mcpSnippet,
  reachedRemote,
  withHostAgent,
  withRemote,
  withoutRemote,
  withLocalAgent
} from '../src/lib/agents.js'

test('an entry is written as qibocal-agent validates it, keeping what the editor does not know', () => {
  const values = { ...agentEditorValues(), platform: ' qw5q ', dependency: 'qibolab-qblox==0.0.4\n\n  other  ', timeout: '600', objective: 'Calibrate.' }
  const { entry, valid } = agentEntry(values, { previous: { report: { port: 8000 }, platform: 'old' } })
  assert.equal(valid, true)
  assert.deepEqual(entry, { report: { port: 8000 }, platform: 'qw5q', dependency: ['qibolab-qblox==0.0.4', 'other'], timeout: 600, objective: 'Calibrate.' })
  assert.equal(Object.values(entry).includes(null), false, 'never a null')
  assert.match(agentEntry({ venv: 'a', server_python: '/p' }).errors.server_python, /not both/)
  assert.match(agentEntry({ slurm_arg: '--time=1' }).errors.slurm_arg, /partition/)
  assert.match(agentEntry({ timeout: '-1' }).errors.timeout, /positive/)
  assert.deepEqual(agentEditorValues({ dependency: ['a', 'b'], platform: 'p' }).dependency, 'a\nb')
})

test('configurations come from agents.json and from those kept for other machines', () => {
  const document = { agents: { default: { platform: 'qutrits' }, tuna: { platform: 'tuna5' } } }
  const hosts = { 'qrc-ws': { agents: { onsite: { platform: 'qw5q' } } } }
  assert.deepEqual(agentConfigurations(document, hosts).map(item => [item.key, item.name, item.host, item.destination]), [
    ['local:default', 'default', 'local', undefined], ['local:tuna', 'tuna', 'local', undefined], ['qrc-ws:onsite', 'onsite', 'qrc-ws', 'qrc-ws']
  ], 'a remote kept before destinations is reached by its name')
  const added = withLocalAgent(document, 'new', { platform: 'x' })
  assert.deepEqual(Object.keys(added.agents), ['default', 'tuna', 'new'])
  assert.equal(document.agents.new, undefined, 'the document given is left alone')
  assert.deepEqual(withLocalAgent(withLocalAgent(document, 'tuna', null), 'default', null), {}, 'nothing left, no empty sections')
  assert.deepEqual(withHostAgent(hosts, 'qrc-ws', 'onsite', null), { 'qrc-ws': { agents: {} } }, 'a remote stays without configurations')
})

test('remotes are named once, and configurations are filtered by where they are kept and what they reach', () => {
  let hosts = withRemote({}, 'lab', ' me@login ')
  hosts = withHostAgent(hosts, 'lab', 'onsite', { platform: 'qw5q' })
  hosts = withRemote(hosts, 'lab', 'me@login2')
  assert.deepEqual(hosts.lab, { ssh: 'me@login2', agents: { onsite: { platform: 'qw5q' } } }, 'a new destination keeps the configurations')
  hosts = withRemote(hosts, 'cluster', 'cluster')
  assert.deepEqual(agentRemotes(hosts), [{ name: 'cluster', ssh: 'cluster', kept: 0 }, { name: 'lab', ssh: 'me@login2', kept: 1 }])
  assert.throws(() => withoutRemote(hosts, 'lab'), /keeps configurations/)
  assert.deepEqual(Object.keys(withoutRemote(hosts, 'cluster')), ['lab'])

  const remotes = agentRemotes(hosts)
  assert.equal(reachedRemote({ ssh: 'me@login2' }, remotes), 'lab')
  assert.equal(reachedRemote({ ssh: 'elsewhere' }, remotes), 'elsewhere', 'a destination with no remote is itself')
  assert.equal(reachedRemote({}, remotes), null)
  const document = { agents: { here: { platform: 'sim' }, there: { platform: 'qw5q', ssh: 'me@login2' } } }
  const items = agentConfigurations(document, hosts)
  const names = filters => items.filter(item => agentShown(item, filters, remotes)).map(item => item.name)
  assert.deepEqual(names({}), ['here', 'there', 'onsite'])
  assert.deepEqual(names({ kept: 'local' }), ['here', 'there'])
  assert.deepEqual(names({ reaches: 'lab' }), ['there'])
  assert.deepEqual(names({ kept: 'lab', reaches: 'direct' }), ['onsite'], 'the two filters together')
  assert.deepEqual(names({ kept: 'local', reaches: 'direct' }), ['here'])
})

test('names, reports, snippet and summary', () => {
  assert.equal(AGENT_NAME.test('tuna-5_a'), true)
  assert.equal(AGENT_NAME.test('-bad'), false)
  assert.equal(agentNameError('default'), '')
  assert.match(agentNameError(''), /needs a name/)
  assert.match(agentNameError('agents'), /reserved/)
  assert.match(agentNameError('-bad'), /letter or digit/)
  assert.equal(agentReports({}, 'tuna'), '~/.local/share/qibocal/agents/runs/tuna')
  assert.equal(agentReports({ output: '/shared/runs' }, 'tuna'), '/shared/runs')
  assert.equal(agentReports({ output: 'mine' }, 'tuna'), '~/.local/share/qibocal/agents/runs/mine')
  assert.equal(agentReports({}), '~/.local/share/qibocal/agents/runs/default')
  // One registration for every configuration, by the absolute path of qibocal-agent.
  assert.deepEqual(JSON.parse(mcpSnippet('/home/me/.cache/qibocal/agents/tools/bin/qibocal-agent')).mcpServers.qibocal,
    { command: '/home/me/.cache/qibocal/agents/tools/bin/qibocal-agent', args: ['mcp'], timeout: 3600000 })
  assert.equal(JSON.parse(mcpSnippet(null)).mcpServers.qibocal.command, 'qibocal-agent', 'none found: the bare command')
  assert.equal(describeAgent({ platform: 'tuna5', ssh: 'qrc-ws', partition: 'qw5q', model: 'openai:gpt-4.1' }), 'platform tuna5 · ssh qrc-ws · partition qw5q · openai:gpt-4.1')
})
