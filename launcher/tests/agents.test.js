import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  AGENT_NAME,
  agentConfigurations,
  agentEditorValues,
  agentEntry,
  agentReports,
  describeAgent,
  mcpSnippet,
  withHostAgent,
  withLocalAgent
} from '../src/lib/agents.js'

test('an entry is written as qibocal-agent validates it, keeping what the editor does not know', () => {
  const values = { ...agentEditorValues(), platform: ' qw5q ', dependency: 'qibolab-qblox==0.0.4\n\n  other  ', timeout: '600', objective: 'Calibrate.' }
  const { entry, valid } = agentEntry(values, { named: true, previous: { report: { port: 8000 }, platform: 'old' } })
  assert.equal(valid, true)
  assert.deepEqual(entry, { report: { port: 8000 }, platform: 'qw5q', dependency: ['qibolab-qblox==0.0.4', 'other'], timeout: 600, objective: 'Calibrate.' })
  assert.equal(agentEntry(values, { named: false }).entry.objective, undefined, 'no objective on the unnamed defaults')
  assert.equal(Object.values(entry).includes(null), false, 'never a null')
  assert.match(agentEntry({ venv: 'a', server_python: '/p' }).errors.server_python, /not both/)
  assert.match(agentEntry({ slurm_arg: '--time=1' }).errors.slurm_arg, /partition/)
  assert.match(agentEntry({ timeout: '-1' }).errors.timeout, /positive/)
  assert.deepEqual(agentEditorValues({ dependency: ['a', 'b'], platform: 'p' }).dependency, 'a\nb')
})

test('configurations come from agent.json and from those kept for other machines', () => {
  const document = { agent: { platform: 'qutrits' }, agents: { tuna: { platform: 'tuna5' } } }
  const hosts = { 'qrc-ws': { agents: { onsite: { platform: 'qw5q' } } } }
  assert.deepEqual(agentConfigurations(document, hosts).map(item => [item.key, item.name, item.host]), [
    ['local:', null, 'local'], ['local:tuna', 'tuna', 'local'], ['qrc-ws:onsite', 'onsite', 'qrc-ws']
  ])
  const added = withLocalAgent(document, 'new', { platform: 'x' })
  assert.deepEqual(Object.keys(added.agents), ['tuna', 'new'])
  assert.equal(document.agents.new, undefined, 'the document given is left alone')
  assert.deepEqual(withLocalAgent(withLocalAgent(document, 'tuna', null), null, null), {}, 'nothing left, no empty sections')
  assert.deepEqual(withHostAgent(hosts, 'qrc-ws', 'onsite', null), {}, 'a host without configurations goes')
})

test('names, reports, snippet and summary', () => {
  assert.equal(AGENT_NAME.test('tuna-5_a'), true)
  assert.equal(AGENT_NAME.test('-bad'), false)
  assert.equal(agentReports({}, 'tuna'), '~/.cache/qibocal/agent/runs/tuna')
  assert.equal(agentReports({ output: '/shared/runs' }, 'tuna'), '/shared/runs')
  assert.equal(agentReports({ output: 'mine' }, 'tuna'), '~/.cache/qibocal/agent/runs/mine')
  assert.equal(agentReports({}, null), '~/.cache/qibocal/agent/runs/default')
  const snippet = JSON.parse(mcpSnippet('tuna', '/x/qibocal-mcp-servers/.venv'))
  assert.equal(snippet.mcpServers.qibocal.command, '/x/qibocal-mcp-servers/.venv/bin/qibocal-mcp-remote')
  assert.deepEqual(snippet.mcpServers.qibocal.args, ['tuna'])
  assert.equal(JSON.parse(mcpSnippet(null)).mcpServers.qibocal.command, 'qibocal-mcp-remote')
  assert.equal(describeAgent({ platform: 'tuna5', ssh: 'qrc-ws', partition: 'qw5q', model: 'openai:gpt-4.1' }), 'platform tuna5 · ssh qrc-ws · partition qw5q · openai:gpt-4.1')
})
