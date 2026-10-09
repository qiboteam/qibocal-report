import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import 'vue-router'

function setupBrowser(url) {
  const location = new URL(url)
  const history = {
    state: null,
    length: 1,
    replaceState(state, title, url) {
      this.state = state
      location.href = new URL(url, location).href
    },
    pushState(state, title, url) {
      this.replaceState(state, title, url)
      this.length++
    }
  }
  globalThis.location = location
  globalThis.window = {
    location,
    history,
    scrollX: 0,
    scrollY: 0,
    addEventListener() {},
    removeEventListener() {}
  }
  globalThis.document = {
    querySelector: () => null,
    addEventListener() {},
    removeEventListener() {}
  }
  globalThis.localStorage = { getItem: () => null, setItem() {}, removeItem() {} }
  globalThis.sessionStorage = { getItem: () => null, setItem() {}, removeItem() {} }
  return location
}

test('routing preserves the entry point and restores shared pages after reload', async t => {
  const globals = ['location', 'window', 'document', 'localStorage', 'sessionStorage']
  const originals = new Map(globals.map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]))
  const vite = await createServer({
    configFile: false,
    root: fileURLToPath(new URL('..', import.meta.url)),
    plugins: [{
      name: 'stub-route-components',
      load(id) {
        if (id.endsWith('.vue')) return 'export default {}'
      }
    }],
    optimizeDeps: { noDiscovery: true },
    server: { middlewareMode: true, hmr: false, watch: null },
    appType: 'custom'
  })

  try {
    for (const entry of [
      'https://qibo.science/qibocal-report/',
      'https://example.com/custom/client/',
      'http://localhost:8000/',
      'file:///tmp/export/index.html'
    ]) {
      await t.test(entry, async () => {
        const location = setupBrowser(entry)
        vite.moduleGraph.invalidateAll()
        let { router } = await vite.ssrLoadModule('/src/router.js')
        let history = router.options.history
        try {
          assert.equal(history.location, '/')
          for (const path of [
            '/servers',
            '/docs',
            '/docs/user-guide/quickstart',
            '/reports/run/subrun?protocol=rabi',
            '/invite?token=example'
          ]) {
            const route = router.resolve(path)
            assert.equal(new URL(route.href, location).pathname, new URL(entry).pathname)
            history.push(route.fullPath)
            assert.equal(location.href, `${entry}#${path}`)
            assert.equal(history.location, path)

            // Recreate the application from its current URL, as a reload would.
            history.destroy()
            window.history.state = null
            vite.moduleGraph.invalidateAll()
            ;({ router } = await vite.ssrLoadModule('/src/router.js'))
            history = router.options.history
            assert.equal(history.location, path)
            const restored = router.resolve(history.location)
            assert.equal(restored.name, route.name)
            assert.deepEqual(restored.params, route.params)
            assert.deepEqual(restored.query, route.query)
          }
        } finally {
          history.destroy()
        }
      })
    }
  } finally {
    await vite.close()
    for (const [key, descriptor] of originals) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor)
      else delete globalThis[key]
    }
  }
})
