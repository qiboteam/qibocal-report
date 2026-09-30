import assert from 'node:assert/strict'
import { test } from 'node:test'
import { ansiSegments } from '../src/utils/ansi.js'
import { readInstallationStream } from '../src/utils/installationStream.js'

test('ANSI renderer preserves standard, bright, 256-color and true-color styles and resets', () => {
  const segments = ansiSegments('\x1b[1;31mError\x1b[0m plain \x1b[94mblue\x1b[38;5;196mred\x1b[38;2;12;34;56mRGB\x1b[39m default')
  assert.equal(segments[0].text, 'Error')
  assert.equal(segments[0].style.fontWeight, 'bold')
  assert.equal(segments[0].style.color, '#f48771')
  assert.deepEqual(segments[1].style, {})
  assert.equal(segments[2].style.color, '#9cdcfe')
  assert.equal(segments[3].style.color, 'rgb(255, 0, 0)')
  assert.equal(segments[4].style.color, 'rgb(12, 34, 56)')
  assert.equal(segments[5].style.color, undefined)
})

test('ANSI renderer strips terminal commands and OSC links without interpreting log text as HTML', () => {
  const text = ansiSegments('\x1b[2J<script>alert("log")</script>\x1b]8;;https://example.org\x07label\x1b]8;;\x1b\\\x1b[0m')
  assert.equal(text.map(segment => segment.text).join(''), '<script>alert("log")</script>label')
  assert.equal(ansiSegments('\x1b[38;5;999mtext')[0].style.color, undefined)
  assert.equal(ansiSegments('\x1b]8;;https://example.org\x1b\\keep\x1b]8;;\x1b\\').map(segment => segment.text).join(''), 'keep')
})

function streamedResponse(chunks, onCancel = () => {}) {
  const encoder = new TextEncoder()
  return new Response(new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(typeof chunk === 'string' ? encoder.encode(chunk) : chunk)
      controller.close()
    },
    cancel: onCancel
  }), { headers: { 'Content-Type': 'application/x-ndjson' } })
}

test('installation stream handles split JSON and UTF-8 while delivering output before completion', async () => {
  const bytes = new TextEncoder().encode(`${JSON.stringify({ type: 'output', text: '\x1b[32mInstalling \u2713\x1b[0m\n' })}\n`)
  const unicode = bytes.indexOf(0xe2)
  const seen = []
  const status = { installed: true, version: '0.2.7', source: 'pypi' }
  const result = await readInstallationStream(streamedResponse([
    bytes.slice(0, unicode + 1), bytes.slice(unicode + 1),
    '{"type":"out', 'put","text":"Done\\n"}\n',
    JSON.stringify({ type: 'complete', status })
  ]), text => seen.push(text))
  assert.deepEqual(seen, ['\x1b[32mInstalling \u2713\x1b[0m\n', 'Done\n'])
  assert.deepEqual(result, status)
})

test('installation progress is delivered while the installer is still running', async () => {
  let controller
  let outputArrived
  const output = new Promise(resolve => { outputArrived = resolve })
  const encoder = new TextEncoder()
  const response = new Response(new ReadableStream({
    start(streamController) { controller = streamController }
  }))
  let finished = false
  const pending = readInstallationStream(response, outputArrived).then(result => {
    finished = true
    return result
  })
  controller.enqueue(encoder.encode('{"type":"output","text":"Collecting qibocal\\n"}\n'))
  assert.equal(await output, 'Collecting qibocal\n')
  assert.equal(finished, false)
  controller.enqueue(encoder.encode('{"type":"complete","status":{"installed":true,"version":"0.2.7","source":"pypi"}}\n'))
  controller.close()
  assert.equal((await pending).version, '0.2.7')
})

test('installer errors and disconnected streams are not treated as success', async () => {
  await assert.rejects(readInstallationStream(Response.json({ detail: 'Admin required' }, { status: 403 }), () => {}), /Admin required/)
  await assert.rejects(readInstallationStream(streamedResponse(['{"type":"output","text":"Starting"}\n']), () => {}), /before completion/)
  await assert.rejects(readInstallationStream(streamedResponse(['{"type":"error","detail":"Installer failed"}\n']), () => {}), /Installer failed/)
  await assert.rejects(readInstallationStream(streamedResponse(['{"type":"complete","status":{"installed":false}}\n']), () => {}), /invalid installation event/)
})

test('installer failure cancels the response reader', async () => {
  let cancelled = false
  const response = new Response(new ReadableStream({
    start(controller) { controller.enqueue(new TextEncoder().encode('{"type":"error","detail":"Failed"}\n')) },
    cancel() { cancelled = true }
  }))
  await assert.rejects(readInstallationStream(response, () => {}), /Failed/)
  assert.equal(cancelled, true)
})
