export function mergeLiveProtocols(protocols, updates, removed = []) {
  const merged = new Map(protocols.map(protocol => [protocol.id, protocol]))
  for (const id of removed) merged.delete(id)
  for (const protocol of updates) merged.set(protocol.id, protocol)
  return [...merged.values()]
}

export function synchronizeLiveProtocols(protocols, snapshot) {
  const existing = new Map(protocols.map(protocol => [protocol.id, protocol]))
  return snapshot.map(protocol => {
    const previous = existing.get(protocol.id)
    return previous && JSON.stringify(previous) === JSON.stringify(protocol)
      ? previous
      : protocol
  })
}

export function createLiveReportSubscription({
  createSocket = url => new WebSocket(url),
  onState,
  onMessage,
  onError,
  setTimer = setTimeout,
  clearTimer = clearTimeout
}) {
  let socket = null
  let timer = null

  function stop() {
    const previous = socket
    socket = null
    if (timer !== null) clearTimer(timer)
    timer = null
    previous?.close()
    onState('inactive')
  }

  function fail(message) {
    stop()
    onError(message)
  }

  function start(url) {
    stop()
    onState('connecting')
    try {
      socket = createSocket(url)
    } catch (error) {
      fail(`Unable to start Live mode: ${error.message}`)
      return
    }
    const current = socket
    timer = setTimer(() => {
      if (socket === current) fail('Live connection timed out. Enable Live to retry.')
    }, 15000)
    current.onmessage = event => {
      if (socket !== current) return
      let message
      try {
        message = JSON.parse(event.data)
      } catch (error) {
        fail(`Invalid Live update: ${error.message}`)
        return
      }
      if (message.type === 'live' && message.active) {
        clearTimer(timer)
        timer = null
        onState('active')
      } else if (message.type === 'error') {
        onError(message.message || 'Live update failed.')
      } else {
        onMessage(message)
      }
    }
    current.onerror = () => {
      if (socket === current) fail('Live connection failed. Enable Live to retry.')
    }
    current.onclose = () => {
      if (socket === current) fail('Live connection closed. Enable Live to retry.')
    }
  }

  return { start, stop }
}
