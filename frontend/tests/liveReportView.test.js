import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import { createRenderer, ref } from 'vue'

test('report Live mode wiring and lifecycle', async t => {
  globalThis.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} }
  globalThis.sessionStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} }
  const vite = await createServer({
    configFile: false,
    root: fileURLToPath(new URL('..', import.meta.url)),
    optimizeDeps: { noDiscovery: true },
    server: { middlewareMode: true, hmr: false, watch: null },
    appType: 'custom'
  })
  const originalSocket = globalThis.WebSocket
  const originalFetch = globalThis.fetch
  const sockets = []
  globalThis.WebSocket = class {
    constructor(url) { this.url = url; this.closed = false; sockets.push(this) }
    close() { this.closed = true }
    message(data) { this.onmessage({ data: JSON.stringify(data) }) }
  }

  try {
    const { state } = await vite.ssrLoadModule('/src/store.js')
    const { useReportDetail } = await vite.ssrLoadModule('/src/composables/useReportDetail.js')

    function mount() {
      state.activeServer = { id: 'server', url: 'http://server.example' }
      state.auth.enabled = false
      state.auth.token = null
      state.auth.user = null
      const id = ref('run')
      let detail
      const renderer = createRenderer({
        createComment: text => ({ text }),
        insert: (node, parent) => { parent.node = node },
        remove: () => {},
        parentNode: () => null,
        nextSibling: () => null
      })
      const app = renderer.createApp({
        setup() {
          detail = useReportDetail(id)
          return () => null
        }
      })
      app.mount({})
      detail.report.value = { id: 'run', history: ['rabi-0', 'ramsey-0'] }
      detail.protocols.value = [
        { id: 'rabi-0', name: 'Rabi', status: 'success', figures: [] },
        { id: 'ramsey-0', name: 'Ramsey', status: 'success', figures: [] }
      ]
      detail.loading.value = false
      return { detail, id, unmount: () => app.unmount() }
    }

    await t.test('toggle acknowledges Live and pushes plots without replacing unaffected protocols', () => {
      const { detail, unmount } = mount()
      const unchanged = detail.protocols.value[1]
      detail.toggleLive()
      const socket = sockets.at(-1)
      assert.match(socket.url, /^ws:\/\/server\.example\/ws\/live\/reports\/run$/)
      assert.equal(detail.live.value, false)
      assert.equal(detail.liveConnecting.value, true)
      socket.message({ type: 'live', active: true })
      assert.equal(detail.live.value, true)
      socket.message({
        type: 'update',
        protocols: [{ id: 'rabi-0', name: 'Rabi', status: 'success', html: 'new', figures: [] }],
        removed: []
      })
      assert.equal(detail.protocols.value[0].html, 'new')
      assert.equal(detail.protocols.value[1], unchanged)
      socket.message({ type: 'error', message: 'Incomplete data' })
      assert.equal(detail.statusBanner.value, 'Incomplete data')
      assert.equal(detail.statusBannerError.value, true)
      detail.toggleLive()
      assert.equal(socket.closed, true)
      assert.equal(detail.live.value, false)
      socket.message({ type: 'update', protocols: [], removed: ['rabi-0'] })
      assert.equal(detail.protocols.value.length, 2)
      unmount()
    })

    await t.test('report, server and session changes and unmount stop monitoring', () => {
      for (const change of [
        ({ id }) => { id.value = 'another-run' },
        () => { state.activeServer.url = 'http://different.example' },
        () => { state.activeServer.id = 'another-server' },
        () => { state.auth.token = 'new-session' },
        () => { state.auth.user = { id: 'new-user', role: 'editor' } },
        () => { state.auth.enabled = true; state.auth.user = { id: 'viewer', role: 'viewer' } },
        ({ unmount }) => unmount()
      ]) {
        const mounted = mount()
        mounted.detail.toggleLive()
        const socket = sockets.at(-1)
        socket.message({ type: 'live', active: true })
        change(mounted)
        assert.equal(socket.closed, true)
        assert.equal(mounted.detail.live.value, false)
        mounted.unmount()
      }
    })

    await t.test('viewers cannot start Live and regeneration stops an active subscription', async () => {
      const { detail, unmount } = mount()
      state.auth.enabled = true
      state.auth.user = { id: 'viewer', role: 'viewer' }
      const before = sockets.length
      detail.toggleLive()
      assert.equal(sockets.length, before)
      state.auth.enabled = false
      detail.toggleLive()
      const socket = sockets.at(-1)
      socket.message({ type: 'live', active: true })
      globalThis.fetch = async () => Response.json([])
      await detail.handleRegenerate()
      assert.equal(socket.closed, true)
      assert.equal(detail.live.value, false)
      unmount()
    })
  } finally {
    globalThis.WebSocket = originalSocket
    globalThis.fetch = originalFetch
    await vite.close()
  }
})
