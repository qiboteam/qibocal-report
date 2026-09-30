import assert from 'node:assert/strict'
import { test, mock } from 'node:test'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createSSRApp, h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { routerKey } from 'vue-router'

test('clicking a cached online card prompts login after enabling auth and browses after disabling it', async () => {
  const storage = new Map()
  globalThis.localStorage = {
    getItem: key => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, String(value)),
    removeItem: key => storage.delete(key)
  }
  globalThis.sessionStorage = { getItem: () => null, setItem: () => {} }
  let enabled = false
  mock.method(globalThis, 'fetch', async url => {
    if (url.endsWith('/api/health')) return new Response('{}')
    if (url.endsWith('/api/auth/status')) {
      return Response.json({ auth_enabled: enabled })
    }
    assert.fail(`Unexpected request: ${url}`)
  })
  const vite = await createServer({
    configFile: false,
    root: fileURLToPath(new URL('..', import.meta.url)),
    plugins: [vue()],
    server: { middlewareMode: true, hmr: false, watch: null },
    appType: 'custom'
  })

  try {
    const store = await vite.ssrLoadModule('/src/store.js')
    const { default: ServersView } = await vite.ssrLoadModule('/src/views/ServersView.vue')
    const { default: ServerCard } = await vite.ssrLoadModule('/src/components/ServerCard.vue')
    const server = { id: 'first', name: 'First', url: 'http://first.example' }
    const push = mock.fn()
    let page
    let card
    let selection
    storage.set('server_connection_first', 'online')
    store.state.servers = [server]
    await store.setActiveServer(server)

    const app = createSSRApp({
      setup() {
        page = ServersView.setup({}, { expose() {} })
        card = ServerCard.setup({ server, isActive: true }, {
          expose() {},
          emit(event, selectedServer) {
            assert.equal(event, 'select')
            selection = page.selectAndNavigate(selectedServer)
          }
        })
        return () => h('div')
      }
    })
    app.provide(routerKey, { push })
    await renderToString(app)

    enabled = true
    card.handleClick()
    await selection
    assert.equal(store.state.auth.showLoginModal, true)
    assert.equal(store.state.auth.errorMessage, '')
    assert.equal(push.mock.callCount(), 0)

    enabled = false
    card.handleClick()
    await selection
    assert.equal(store.state.auth.showLoginModal, false)
    assert.equal(store.canEdit.value, true)
    assert.equal(push.mock.calls[0].arguments[0], '/dashboard')
    assert.equal(store.state.servers.length, 1)
  } finally {
    await vite.close()
    mock.restoreAll()
  }
})
