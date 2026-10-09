import assert from 'node:assert/strict'
import test from 'node:test'
import { createLiveReportSubscription, mergeLiveProtocols, synchronizeLiveProtocols } from '../src/utils/liveReport.js'

function subscription() {
  const sockets = []
  const states = []
  const messages = []
  const errors = []
  let timeout
  const controller = createLiveReportSubscription({
    createSocket(url) {
      const socket = { url, closed: false, close() { this.closed = true } }
      sockets.push(socket)
      return socket
    },
    onState: state => states.push(state),
    onMessage: message => messages.push(message),
    onError: error => errors.push(error),
    setTimer: callback => { timeout = callback; return 1 },
    clearTimer: () => {},
  })
  const send = (socket, message) => socket.onmessage({ data: JSON.stringify(message) })
  return { controller, sockets, states, messages, errors, send, expire: () => timeout() }
}

test('updates merge by task id, preserving unchanged objects and removing deleted tasks', () => {
  const unchanged = { id: 'rabi-0', figures: [{ data: [1] }] }
  const changed = { id: 'ramsey-0', figures: [{ data: [2] }] }
  const updated = { id: 'ramsey-0', figures: [{ data: [3] }] }
  const added = { id: 'rabi-1', figures: [] }
  const result = mergeLiveProtocols(
    [unchanged, changed, { id: 'removed' }], [updated, added], ['removed']
  )
  assert.deepEqual(result, [unchanged, updated, added])
  assert.equal(result[0], unchanged)
})

test('subscription snapshots replay missed updates and removals without rerendering unchanged plots', () => {
  const unchanged = { id: 'rabi-0', figures: [{ data: [1] }] }
  const changed = { id: 'ramsey-0', figures: [{ data: [2] }] }
  const updated = { id: 'ramsey-0', figures: [{ data: [3] }] }
  const result = synchronizeLiveProtocols(
    [unchanged, changed, { id: 'deleted' }],
    [JSON.parse(JSON.stringify(unchanged)), updated]
  )
  assert.deepEqual(result, [unchanged, updated])
  assert.equal(result[0], unchanged)
  assert.equal(result[1], updated)
})
test('Live becomes active only after acknowledgement', () => {
  const { controller, sockets, states, send } = subscription()
  controller.start('ws://server/ws/live/reports/run?token=example')
  assert.equal(sockets[0].url, 'ws://server/ws/live/reports/run?token=example')
  assert.equal(states.at(-1), 'connecting')
  send(sockets[0], { type: 'live', active: true })
  assert.equal(states.at(-1), 'active')
})

test('stopped and replaced subscriptions ignore stale events', () => {
  const { controller, sockets, messages, errors, send } = subscription()
  controller.start('ws://first')
  controller.stop()
  assert.equal(sockets[0].closed, true)
  send(sockets[0], { type: 'update', protocols: [{ id: 'stale' }] })
  sockets[0].onclose()
  controller.start('ws://second')
  sockets[0].onerror()
  send(sockets[1], { type: 'metadata', report: { id: 'current' } })
  assert.deepEqual(messages, [{ type: 'metadata', report: { id: 'current' } }])
  assert.deepEqual(errors, [])
})

test('disconnects and connection timeouts stop Live and surface errors', () => {
  const { controller, sockets, states, errors, expire } = subscription()
  controller.start('ws://server')
  expire()
  assert.equal(states.at(-1), 'inactive')
  assert.equal(sockets[0].closed, true)
  assert.match(errors[0], /timed out/)
  controller.start('ws://server')
  sockets[1].onclose()
  assert.equal(states.at(-1), 'inactive')
  assert.match(errors[1], /closed/)
})

test('transient generation errors are visible without disabling the subscription', () => {
  const { controller, sockets, states, errors, messages, send } = subscription()
  controller.start('ws://server')
  send(sockets[0], { type: 'live', active: true })
  send(sockets[0], { type: 'error', message: 'Data is still being written' })
  assert.equal(states.at(-1), 'active')
  assert.deepEqual(errors, ['Data is still being written'])
  send(sockets[0], { type: 'update', protocols: [{ id: 'rabi' }], removed: [] })
  assert.equal(messages.length, 1)
})

test('invalid payload and socket errors do not leave an active recording light', () => {
  const { controller, sockets, states, errors } = subscription()
  controller.start('ws://server')
  sockets[0].onmessage({ data: '{' })
  assert.equal(states.at(-1), 'inactive')
  assert.match(errors[0], /Invalid Live update/)
  controller.start('ws://server')
  sockets[1].onerror()
  assert.equal(states.at(-1), 'inactive')
  assert.match(errors[1], /connection failed/)
})
