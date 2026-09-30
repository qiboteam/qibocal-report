import assert from 'node:assert/strict'
import { test, mock } from 'node:test'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createSSRApp, h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { routerKey } from 'vue-router'

function setupStorage() {
  const storage = new Map()
  globalThis.localStorage = {
    getItem: key => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, String(value)),
    removeItem: key => storage.delete(key)
  }
  globalThis.sessionStorage = { getItem: () => null, setItem: () => {} }
  return storage
}

function createTestServer() {
  return createServer({
    configFile: false,
    root: fileURLToPath(new URL('..', import.meta.url)),
    plugins: [vue()],
    server: { middlewareMode: true, hmr: false, watch: null },
    appType: 'custom'
  })
}

test('clicking a cached online card prompts login after enabling auth and browses after disabling it', async () => {
  const storage = setupStorage()
  let enabled = false
  mock.method(globalThis, 'fetch', async url => {
    if (url.endsWith('/api/health')) return new Response('{}')
    if (url.endsWith('/api/auth/status')) {
      return Response.json({ auth_enabled: enabled })
    }
    assert.fail(`Unexpected request: ${url}`)
  })
  const vite = await createTestServer()

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

test('server cards show auth-only administration and the appropriate lock beside the name', async t => {
  setupStorage()
  let enabled = false
  mock.method(globalThis, 'fetch', async url => {
    if (url.endsWith('/api/health')) return Response.json({ reports_count: 1 })
    if (url.endsWith('/api/auth/status')) return Response.json({ auth_enabled: enabled })
    assert.fail(`Unexpected request: ${url}`)
  })
  const vite = await createTestServer()

  try {
    const store = await vite.ssrLoadModule('/src/store.js')
    const { default: ServerCard } = await vite.ssrLoadModule('/src/components/ServerCard.vue')
    const server = { id: 'first', name: 'First', url: 'http://first.example' }

    for (const [name, authEnabled, signedIn, isActive = false] of [
      ['open server', false, false],
      ['signed-out auth server', true, false],
      ['signed-in auth server', true, true],
      ['open server after disabling auth', false, false, true]
    ]) {
      await t.test(name, async () => {
        enabled = authEnabled
        store.state.auth.enabled = true
        store.state.auth.checked = true
        store.setServerAuth(server, signedIn ? 'session' : null,
          signedIn ? { id: 'user', username: 'user', role: 'viewer' } : null)
        const html = await renderToString(createSSRApp({
          ...ServerCard,
          async setup(props, context) {
            const card = ServerCard.setup(props, context)
            card.menuOpen.value = true
            await card.checkHealth()
            return card
          }
        }, { server, isActive }))

        assert.equal(html.includes('Administer'), authEnabled)
        if (authEnabled) {
          const label = signedIn ? 'Signed in' : 'Authentication required'
          assert.ok(html.includes(`aria-label="${label}"`))
          assert.ok(html.indexOf(`aria-label="${label}"`) < html.indexOf('<h3'))
          assert.equal(html.includes('d="M10 11V7a4 4 0 00-8 0v2'), signedIn)
          assert.equal(html.includes('Log out'), signedIn)
        } else {
          assert.equal(html.includes('role="img"'), false)
          assert.equal(html.includes('Log out'), false)
        }
      })
    }
  } finally {
    await vite.close()
    mock.restoreAll()
  }
})

test('clicking a card during its initial status refresh queues selection', async () => {
  setupStorage()
  let resolveHealth
  mock.method(globalThis, 'fetch', async url => {
    if (url.endsWith('/api/health')) return new Promise(resolve => { resolveHealth = resolve })
    if (url.endsWith('/api/auth/status')) return Response.json({ auth_enabled: true })
    assert.fail(`Unexpected request: ${url}`)
  })
  const vite = await createTestServer()

  try {
    const { default: ServerCard } = await vite.ssrLoadModule('/src/components/ServerCard.vue')
    const server = { id: 'first', name: 'First', url: 'http://first.example' }
    const emit = mock.fn()
    let card
    await renderToString(createSSRApp({
      setup() {
        card = ServerCard.setup({ server, isActive: false }, { expose() {}, emit })
        return () => h('div')
      }
    }))
    const checking = card.checkHealth()
    card.handleClick()
    assert.equal(emit.mock.callCount(), 0)
    resolveHealth(Response.json({ reports_count: 1 }))
    await checking
    assert.deepEqual(emit.mock.calls[0].arguments, ['select', server])
  } finally {
    await vite.close()
    mock.restoreAll()
  }
})

test('a status response for an old server URL cannot overwrite the refreshed card', async () => {
  setupStorage()
  let resolveOldHealth
  mock.method(globalThis, 'fetch', async url => {
    if (url === 'http://old.example/api/health') {
      return new Promise(resolve => { resolveOldHealth = resolve })
    }
    if (url.endsWith('/api/health')) return Response.json({ reports_count: 2 })
    return Response.json({ auth_enabled: url.startsWith('http://old.example') })
  })
  const vite = await createTestServer()

  try {
    const { default: ServerCard } = await vite.ssrLoadModule('/src/components/ServerCard.vue')
    const props = {
      server: { id: 'first', name: 'First', url: 'http://old.example' },
      isActive: false
    }
    let card
    await renderToString(createSSRApp({
      setup() {
        card = ServerCard.setup(props, { expose() {}, emit() {} })
        return () => h('div')
      }
    }))
    const oldCheck = card.checkHealth()
    props.server.url = 'http://new.example'
    card.isChecking.value = false
    await card.checkHealth()
    resolveOldHealth(Response.json({ reports_count: 1 }))
    await oldCheck
    assert.equal(card.requiresAuth.value, false)
    assert.equal(card.reportCount.value, 2)
    assert.equal(card.connectionStatus.value, 'online')
  } finally {
    await vite.close()
    mock.restoreAll()
  }
})
