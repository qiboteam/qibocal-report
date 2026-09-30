export async function readInstallationStream(response, onOutput) {
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || `Qibocal request failed (${response.status})`)
  }
  if (!response.body) throw new Error('The server did not provide installation output.')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let pending = ''
  let status = null
  function consume(line) {
    if (!line.trim()) return
    const event = JSON.parse(line)
    if (event.type === 'output' && typeof event.text === 'string') onOutput(event.text)
    else if (event.type === 'complete' && event.status?.installed && event.status.version) status = event.status
    else if (event.type === 'error') throw new Error(event.detail || 'Qibocal installation failed.')
    else throw new Error('The server sent an invalid installation event.')
  }
  try {
    while (true) {
      const { value, done } = await reader.read()
      pending += done ? decoder.decode() : decoder.decode(value, { stream: true })
      let newline
      while ((newline = pending.indexOf('\n')) !== -1) {
        consume(pending.slice(0, newline))
        pending = pending.slice(newline + 1)
      }
      if (pending.length > 1_000_000) throw new Error('The installation output exceeded the stream limit.')
      if (done) break
    }
    if (pending.trim()) consume(pending)
    if (!status) throw new Error('Installation connection closed before completion. Check the server logs before retrying.')
    return status
  } finally {
    try {
      await reader.cancel()
    } finally {
      reader.releaseLock()
    }
  }
}
