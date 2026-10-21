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
  mcpSnippet,
  withHostAgent,
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
  assert.deepEqual(agentConfigurations(document, hosts).map(item => [item.key, item.name, item.host]), [
    ['local:default', 'default', 'local'], ['local:tuna', 'tuna', 'local'], ['qrc-ws:onsite', 'onsite', 'qrc-ws']
  ])
  const added = withLocalAgent(document, 'new', { platform: 'x' })
  assert.deepEqual(Object.keys(added.agents), ['default', 'tuna', 'new'])
  assert.equal(document.agents.new, undefined, 'the document given is left alone')
  assert.deepEqual(withLocalAgent(withLocalAgent(document, 'tuna', null), 'default', null), {}, 'nothing left, no empty sections')
  assert.deepEqual(withHostAgent(hosts, 'qrc-ws', 'onsite', null), {}, 'a host without configurations goes')
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
  const snippet = JSON.parse(mcpSnippet('tuna', '/x/qibocal-mcp-servers/.venv'))
  assert.equal(snippet.mcpServers.qibocal.command, '/x/qibocal-mcp-servers/.venv/bin/qibocal-agent')
  assert.deepEqual(snippet.mcpServers.qibocal.args, ['mcp', 'tuna'])
  assert.deepEqual(JSON.parse(mcpSnippet('default')).mcpServers.qibocal, { command: 'qibocal-agent', args: ['mcp'], timeout: 3600000 })
  assert.equal(JSON.parse(mcpSnippet('tuna', '/e/bin/qibocal-agent')).mcpServers.qibocal.command, '/e/bin/qibocal-agent', 'the executable itself')
  assert.equal(JSON.parse(mcpSnippet('tuna', '/c/envs/qibocal-agent')).mcpServers.qibocal.command, '/c/envs/qibocal-agent/bin/qibocal-agent', 'an environment named after it')
  assert.equal(describeAgent({ platform: 'tuna5', ssh: 'qrc-ws', partition: 'qw5q', model: 'openai:gpt-4.1' }), 'platform tuna5 · ssh qrc-ws · partition qw5q · openai:gpt-4.1')
})
