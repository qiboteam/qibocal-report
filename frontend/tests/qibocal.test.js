import assert from 'node:assert/strict'
import { test, mock } from 'node:test'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createSSRApp, createRenderer, h, ref, nextTick, ssrContextKey } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { createRouter, createMemoryHistory } from 'vue-router'

function setupStorage() {
  globalThis.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} }
  globalThis.sessionStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} }
}

test('Qibocal administration and plot-generation feedback', async t => {
  setupStorage()
  const vite = await createServer({
    configFile: false,
    root: fileURLToPath(new URL('..', import.meta.url)),
    plugins: [
      {
        name: 'plotly-test-stub',
        enforce: 'pre',
        resolveId: id => id === 'plotly.js-dist-min' ? '\0plotly-test-stub' : null,
        load: id => id === '\0plotly-test-stub' ? 'export default {}' : null
      },
      vue()
    ],
    ssr: { noExternal: ['plotly.js-dist-min'] },
    optimizeDeps: { noDiscovery: true },
    server: { middlewareMode: true, hmr: false, watch: null },
    appType: 'custom'
  })

  try {
    const store = await vite.ssrLoadModule('/src/store.js')
    const { useQibocalEnvironment } = await vite.ssrLoadModule('/src/composables/useQibocalEnvironment.js')
    const { useReportDetail } = await vite.ssrLoadModule('/src/composables/useReportDetail.js')
    const { default: PreviewModal } = await vite.ssrLoadModule('/src/components/modals/PreviewModal.vue')
    const { default: AdminFooter } = await vite.ssrLoadModule('/src/components/diagnostics/AdminFooter.vue')
    const { default: QibocalPanel } = await vite.ssrLoadModule('/src/components/diagnostics/QibocalPanel.vue')
    const { default: AnsiOutput } = await vite.ssrLoadModule('/src/components/diagnostics/AnsiOutput.vue')
    const { diagnostics } = await vite.ssrLoadModule('/src/composables/useDiagnostics.js')
    const { default: ReportView } = await vite.ssrLoadModule('/src/views/ReportView.vue')
    const { getPlotGenerationErrors, isQibocalMissing } = await vite.ssrLoadModule('/src/utils/plotGeneration.js')
    const first = { id: 'first', name: 'First', url: 'http://first.example' }
    const second = { id: 'second', name: 'Second', url: 'http://second.example' }
    const missing = {
      id: 'rabi', name: 'Rabi', status: 'error', figures: [],
      error: 'Qibocal is not installed in the environment.',
      error_code: 'qibocal_not_installed'
    }
    const choices = {
      installed: false, version: null, source: null,
      options: [
        { id: 'pypi:0.2.5', label: 'Qibocal 0.2.5 (PyPI)', source: 'pypi', version: '0.2.5' },
        { id: 'git', label: 'Git repository (latest)', source: 'git', version: null }
      ],
      pypi_error: null
    }
    const installationResponse = status => new Response(
      `${JSON.stringify({ type: 'output', text: '\x1b[32mInstalling qibocal\x1b[0m\n' })}\n${JSON.stringify({ type: 'complete', status })}\n`,
      { headers: { 'Content-Type': 'application/x-ndjson' } }
    )

    function setRole(role, enabled = true, checked = true) {
      store.state.activeServer = first
      store.state.auth.enabled = enabled
      store.state.auth.checked = checked
      store.setServerAuth(first, role ? `${role}-session` : null,
        role ? { id: role, username: role, role } : null)
    }

    async function setupComposable(factory) {
      let result
      await renderToString(createSSRApp({
        setup() {
          result = factory()
          return () => h('div')
        }
      }))
      return result
    }

    function mountComposable(factory, plugins = []) {
      let result
      const renderer = createRenderer({
        createComment: text => ({ text }),
        insert: (node, parent) => { parent.node = node },
        remove: () => {},
        parentNode: () => null,
        nextSibling: () => null
      })
      const app = renderer.createApp({
        setup() {
          result = factory()
          return () => null
        }
      })
      app.provide(ssrContextKey, { modules: new Set() })
      for (const plugin of plugins) app.use(plugin)
      app.mount({})
      return { result, unmount: () => app.unmount() }
    }

    await t.test('only a verified signed-in administrator can change the environment', async () => {
      for (const [role, enabled, checked, expected] of [
        ['admin', true, true, true],
        ['viewer', true, true, false],
        ['editor', true, true, false],
        [null, true, true, false],
        ['admin', false, true, false],
        ['admin', true, false, false]
      ]) {
        setRole(role, enabled, checked)
        assert.equal(store.canManageQibocal.value, expected)
        mock.method(globalThis, 'fetch', async () => Response.json({ installed: false }))
        diagnostics.expanded = false
        const html = await renderToString(createSSRApp(AdminFooter))
        assert.equal(html.includes('Administrator diagnostics'), expected)
        if (expected) {
          assert.match(html, /height:8px/)
          assert.match(html, /aria-valuenow="8"/)
          assert.match(html, /Server logs/)
          assert.match(html, /role="tab"/)
          assert.equal(html.includes('type="range"'), false)
          assert.equal(html.includes('Collapse diagnostics panel'), false)
        }
        mock.restoreAll()
      }
    })

    await t.test('preview explicitly shows missing Qibocal instead of the empty-figures message', async () => {
      setRole('viewer')
      mock.method(globalThis, 'fetch', async () => Response.json([missing, { ...missing, id: 'ramsey' }]))
      const html = await renderToString(createSSRApp({
        ...PreviewModal,
        async setup(props, context) {
          const preview = PreviewModal.setup(props, context)
          await preview.loadPreview()
          return preview
        }
      }, { show: true, report: { id: 'run' } }))
      assert.match(html, /Qibocal is not installed on this server/)
      assert.match(html, /Ask a server administrator/)
      assert.equal(html.includes('No figures available to preview'), false)
      assert.equal(html.includes('Install Qibocal'), false)
      assert.equal((html.match(/Qibocal is not installed in the environment\./g) || []).length, 1)
      mock.restoreAll()
    })

    await t.test('preview retains plots alongside failures and offers admin installation', async () => {
      setRole('admin')
      mock.method(globalThis, 'fetch', async url => url.endsWith('/api/qibocal')
        ? Response.json({ installed: false })
        : Response.json([missing, { id: 'good', name: 'Working routine', figures: [{ id: 'fig', title: 'Working plot' }] }]))
      const html = await renderToString(createSSRApp({
        ...PreviewModal,
        async setup(props, context) {
          const preview = PreviewModal.setup(props, context)
          await preview.loadPreview()
          return preview
        }
      }, { show: true, report: { id: 'run' } }))
      assert.match(html, /Working plot/)
      assert.match(html, /Qibocal is not installed/)
      assert.match(html, /Drag the bottom diagnostics handle upward/)
      mock.restoreAll()
    })

    await t.test('generic failures are not incorrectly described as missing Qibocal', () => {
      assert.equal(isQibocalMissing([missing]), true)
      assert.equal(isQibocalMissing([{ error: missing.error }]), true)
      assert.equal(isQibocalMissing([{ error: 'Error importing Qibocal: missing qibolab' }]), false)
      assert.deepEqual(getPlotGenerationErrors([{ id: 'rabi', status: 'error' }]), ['Plot generation failed for rabi.'])
    })

    await t.test('full report displays missing Qibocal and keeps version controls admin-only', async () => {
      const router = createRouter({
        history: createMemoryHistory(),
        routes: [
          { path: '/reports/:id', component: { render: () => h('div') } },
          { path: '/:pathMatch(.*)*', component: { render: () => h('div') } }
        ]
      })
      await router.push('/reports/run')
      for (const role of ['viewer', 'admin']) {
        setRole(role)
        mock.method(globalThis, 'fetch', async () => Response.json({ installed: false }))
        const app = createSSRApp({
          ...ReportView,
          setup(props, context) {
            const report = ReportView.setup(props, context)
            report.loading.value = false
            report.report.value = { id: 'run', targets: [0], platform: 'test', date: '2026-09-30' }
            report.protocols.value = [missing]
            return report
          }
        })
        app.use(router)
        const html = await renderToString(app)
        assert.match(html, /Qibocal is not installed on this server/)
        assert.equal(html.includes('Drag the bottom diagnostics handle upward'), role === 'admin')
        mock.restoreAll()
      }
    })

    await t.test('footer picker streams output and signals confirmed installation without closing the panel', async () => {
      setRole('admin')
      const installed = mock.fn()
      mock.method(globalThis, 'fetch', async (url, options) => {
        if (url.endsWith('/api/qibocal')) return Response.json({ installed: true, version: '0.2.4', source: 'pypi' })
        if (url.endsWith('/options')) return Response.json(choices)
        assert.equal(url, `${first.url}/api/admin/qibocal/install/stream`)
        assert.equal(options.headers.get('Authorization'), 'Bearer admin-session')
        assert.deepEqual(JSON.parse(options.body), { option: 'pypi:0.2.5' })
        return installationResponse({ installed: true, version: '0.2.5', source: 'pypi' })
      })
      const environment = await setupComposable(() => useQibocalEnvironment(installed))
      await environment.refreshOptions()
      assert.deepEqual(environment.options.value.map(option => option.id), ['pypi:0.2.5', 'git'])
      assert.equal(environment.selected.value, 'pypi:0.2.5')
      await environment.install()
      assert.equal(environment.environment.value.version, '0.2.5')
      assert.match(environment.installOutput.value, /Installing qibocal/)
      assert.match(environment.success.value, /0\.2\.5 installed successfully/)
      assert.equal(installed.mock.callCount(), 1)
      assert.equal(environment.installing.value, false)
      mock.restoreAll()
    })

    await t.test('installation errors are visible and do not regenerate; Git remains selectable when PyPI fails', async () => {
      setRole('admin')
      const installed = mock.fn()
      mock.method(globalThis, 'fetch', async (url, options) => {
        if (url.endsWith('/api/qibocal')) return Response.json({ installed: false })
        if (url.endsWith('/options')) return Response.json({
          ...choices, options: [choices.options[1]], pypi_error: 'PyPI is unavailable.'
        })
        assert.deepEqual(JSON.parse(options.body), { option: 'git' })
        return Response.json({ detail: 'Server environment is read-only.' }, { status: 500 })
      })
      const environment = await setupComposable(() => useQibocalEnvironment(installed))
      await environment.refreshOptions()
      assert.equal(environment.pypiError.value, 'PyPI is unavailable.')
      assert.equal(environment.selected.value, 'git')
      await environment.install()
      assert.equal(environment.error.value, 'Server environment is read-only.')
      assert.equal(installed.mock.callCount(), 0)
      mock.restoreAll()
    })

    await t.test('the Qibocal tab displays the current version, sources and a persistent installer console', async () => {
      setRole('admin')
      mock.method(globalThis, 'fetch', async url => Response.json(url.endsWith('/options')
        ? { ...choices, installed: true, version: '0.2.4', source: 'pypi' }
        : { installed: true, version: '0.2.4', source: 'pypi' }))
      diagnostics.expanded = true
      diagnostics.tab = 'qibocal'
      const html = await renderToString(createSSRApp({
        ...QibocalPanel,
        async setup(props, setupContext) {
          const controls = QibocalPanel.setup(props, setupContext)
          await controls.refreshOptions()
          return controls
        }
      }))
      assert.match(html, /Current version:.*0\.2\.4/)
      assert.match(html, /Qibocal 0\.2\.5 \(PyPI\)/)
      assert.match(html, /Git repository \(latest\)/)
      assert.match(html, /Install \/ Switch version/)
      assert.match(html, /for all users/)
      assert.match(html, /Qibocal installation output/)
      assert.equal((html.match(/<select/g) || []).length, 1)
      assert.match(html, /aria-label="Qibocal Git branch"/)
      assert.match(html, /class="git-source/)
      assert.equal((html.match(/role="radio"/g) || []).length, 2)
      assert.equal((html.match(/aria-checked="true"/g) || []).length, 1)
      assert.match(html, /alt="Qibocal 0\.2\.5 \(PyPI\)"/)
      assert.match(html, /<span[^>]*>0\.2\.5<\/span>/)
      assert.match(html, /aria-label="Reload versions"/)
      assert.match(html, /title="Install \/ Switch version"/)
      assert.match(html, /<span[^>]*>Install<\/span>/)
      assert.match(html, /<span[^>]*>Refresh<\/span>/)
      assert.equal(html.includes('>Reload versions<'), false)
      assert.equal(html.includes('>Install / Switch version<'), false)
      assert.ok(html.indexOf('for all users') > html.indexOf('title="Install / Switch version"'))
      assert.equal(html.includes('keep this dialog open'), false)
      diagnostics.expanded = false
      mock.restoreAll()
    })

    await t.test('the picker shows six PyPI versions and a separate Git branch row', async () => {
      setRole('admin')
      const extended = {
        ...choices,
        options: [
          ...['0.2.9', '0.2.8', '0.2.7', '0.2.6', '0.2.5', '0.1.7'].map(version => ({
            id: `pypi:${version}`, label: `Qibocal ${version} (PyPI)`, source: 'pypi', version
          })),
          choices.options[1]
        ],
        git_branches: ['main', '0.1', 'feature/branch'],
        git_default_branch: 'main',
        github_error: null
      }
      mock.method(globalThis, 'fetch', async url => Response.json(url.endsWith('/options') ? extended : { installed: false }))
      try {
        const html = await renderToString(createSSRApp({
          ...QibocalPanel,
          async setup(props, context) {
            const controls = QibocalPanel.setup(props, context)
            await controls.refreshOptions()
            return controls
          }
        }))
        assert.equal((html.match(/class="pypi-logo"/g) || []).length, 6)
        assert.equal((html.match(/role="radio"/g) || []).length, 7)
        assert.match(html, /<span[^>]*>0\.1\.7<\/span>/)
        assert.match(html, /Git: main/)
        assert.match(html, /<option value="feature\/branch"/)
        assert.match(html, /<option value="0\.1"/)
      } finally {
        mock.restoreAll()
      }
    })

    await t.test('Git installation submits the chosen branch and rejects names outside the offered list', async () => {
      setRole('admin')
      const installed = mock.fn()
      const fetch = mock.method(globalThis, 'fetch', async (url, request) => {
        if (url.endsWith('/api/qibocal')) return Response.json({ installed: false })
        if (url.endsWith('/options')) return Response.json({
          ...choices, git_branches: ['main', '0.1', 'feature/branch'], git_default_branch: 'main'
        })
        assert.deepEqual(JSON.parse(request.body), { option: 'git:feature/branch' })
        return installationResponse({ installed: true, version: '0.2.8.dev1', source: 'git' })
      })
      try {
        const environment = await setupComposable(() => useQibocalEnvironment(installed))
        await environment.refreshOptions()
        assert.equal(environment.gitBranch.value, 'main')
        environment.selected.value = 'git'
        environment.gitBranch.value = 'not-listed'
        await environment.install()
        assert.equal(fetch.mock.calls.some(call => call.arguments[0].endsWith('/install/stream')), false)
        assert.match(environment.error.value, /available Qibocal Git branches/)
        environment.gitBranch.value = 'feature/branch'
        await environment.install()
        assert.equal(installed.mock.callCount(), 1)
      } finally {
        mock.restoreAll()
      }
    })

    await t.test('version buttons support radio-style keyboard selection and lock while installing', async () => {
      setRole('admin')
      diagnostics.expanded = false
      mock.method(globalThis, 'fetch', async url => Response.json(url.endsWith('/options') ? choices : { installed: false }))
      try {
        const controls = await setupComposable(() => QibocalPanel.setup({}, { emit() {}, expose() {} }))
        await controls.refreshOptions()
        const event = key => ({ key, preventDefault() {} })
        await controls.selectSource(event('ArrowRight'), 0)
        assert.equal(controls.selected.value, 'git')
        await controls.selectSource(event('Home'), 1)
        assert.equal(controls.selected.value, 'pypi:0.2.5')
        controls.installing.value = true
        await controls.selectSource(event('End'), 0)
        assert.equal(controls.selected.value, 'pypi:0.2.5')
      } finally {
        diagnostics.installing = false
        mock.restoreAll()
      }
    })

    await t.test('installation can be collapsed without duplication, and old server results are ignored', async () => {
      setRole('admin')
      let finishInstall
      const installed = mock.fn()
      const fetch = mock.method(globalThis, 'fetch', async url => {
        if (url.endsWith('/api/qibocal')) return Response.json({ installed: false })
        if (url.endsWith('/options')) return Response.json(choices)
        return new Promise(resolve => { finishInstall = resolve })
      })
      const environment = await setupComposable(() => useQibocalEnvironment(installed))
      await environment.refreshOptions()
      diagnostics.expanded = true
      const pending = environment.install()
      await environment.install()
      diagnostics.expanded = false
      assert.equal(diagnostics.expanded, false)
      assert.equal(environment.installing.value, true)
      assert.equal(fetch.mock.calls.filter(call => call.arguments[0].endsWith('/install/stream')).length, 1)
      store.state.activeServer = second
      finishInstall(installationResponse({ installed: true, version: '0.2.5', source: 'pypi' }))
      await pending
      assert.equal(installed.mock.callCount(), 0)
      assert.equal(environment.environment.value.installed, false)
      mock.restoreAll()
    })

    await t.test('dragging opens, resizes and collapses the footer; clicking never toggles it', async () => {
      setRole('admin')
      diagnostics.expanded = false
      const footer = await setupComposable(() => AdminFooter.setup({}, { emit() {}, expose() {} }))
      let captured = false
      const handle = {
        setPointerCapture() { captured = true },
        hasPointerCapture() { return captured },
        releasePointerCapture() { captured = false }
      }
      const event = y => ({
        button: 0, isPrimary: true, pointerId: 1, clientY: y,
        currentTarget: handle, preventDefault() {}
      })
      footer.startResize(event(800))
      footer.finishResize(event(800))
      assert.equal(diagnostics.expanded, false)
      assert.equal(footer.displayedHeight.value, 8)
      footer.startResize(event(800))
      footer.resize(event(500))
      footer.finishResize(event(500))
      assert.equal(diagnostics.expanded, true)
      assert.equal(footer.displayedHeight.value, 308)
      footer.startResize(event(500))
      footer.finishResize(event(500))
      assert.equal(diagnostics.expanded, true)
      assert.equal(footer.displayedHeight.value, 308)
      footer.startResize(event(500))
      footer.resize(event(450))
      footer.finishResize(event(450))
      assert.equal(footer.displayedHeight.value, 358)
      footer.startResize(event(450))
      footer.resize(event(800))
      footer.finishResize(event(800))
      assert.equal(diagnostics.expanded, false)
      assert.equal(footer.displayedHeight.value, 8)
      assert.equal(captured, false)
    })

    await t.test('live progress survives normal navigation and collapsing and still signals successful installation', async () => {
      setRole('admin')
      store.state.servers = [first]
      let controller
      const installed = mock.fn()
      mock.method(globalThis, 'fetch', async url => {
        if (url.endsWith('/api/auth/status')) return Response.json({ auth_enabled: true })
        if (url.endsWith('/api/auth/me')) return Response.json({ id: 'admin', username: 'admin', role: 'admin' })
        if (url.endsWith('/api/qibocal')) return Response.json({ installed: false })
        if (url.endsWith('/options')) return Response.json(choices)
        return new Response(new ReadableStream({ start(value) { controller = value } }))
      })
      const { result: environment, unmount } = mountComposable(() => useQibocalEnvironment(installed))
      try {
        await environment.refreshOptions()
        diagnostics.expanded = true
        const pending = environment.install()
        await nextTick()
        controller.enqueue(new TextEncoder().encode('{"type":"output","text":"Downloading qibocal\\n"}\n'))
        await new Promise(resolve => setImmediate(resolve))
        assert.match(environment.installOutput.value, /Downloading qibocal/)
        assert.equal(environment.installing.value, true)
        await store.fetchServers()
        assert.match(environment.installOutput.value, /Downloading qibocal/)
        assert.equal(environment.installing.value, true)
        diagnostics.expanded = false
        controller.enqueue(new TextEncoder().encode('{"type":"complete","status":{"installed":true,"version":"0.2.5","source":"pypi"}}\n'))
        controller.close()
        await pending
        assert.equal(environment.environment.value.version, '0.2.5')
        assert.equal(environment.installing.value, false)
        assert.equal(installed.mock.callCount(), 1)
      } finally {
        unmount()
        mock.restoreAll()
      }
    })

    await t.test('revoking the admin session clears installer output and ignores a late completion', async () => {
      setRole('admin')
      let controller
      const installed = mock.fn()
      mock.method(globalThis, 'fetch', async url => {
        if (url.endsWith('/api/qibocal')) return Response.json({ installed: false })
        if (url.endsWith('/options')) return Response.json(choices)
        return new Response(new ReadableStream({ start(value) { controller = value } }))
      })
      const { result: environment, unmount } = mountComposable(() => useQibocalEnvironment(installed))
      try {
        await environment.refreshOptions()
        const pending = environment.install()
        await nextTick()
        controller.enqueue(new TextEncoder().encode('{"type":"output","text":"Installing\\n"}\n'))
        await new Promise(resolve => setImmediate(resolve))
        assert.equal(environment.installOutput.value, 'Installing\n')
        store.setServerAuth(first, null, null)
        assert.equal(environment.installOutput.value, '')
        assert.equal(environment.environment.value, null)
        controller.enqueue(new TextEncoder().encode('{"type":"complete","status":{"installed":true,"version":"0.2.5","source":"pypi"}}\n'))
        controller.close()
        await pending
        assert.equal(installed.mock.callCount(), 0)
        assert.equal(environment.environment.value, null)
      } finally {
        unmount()
        mock.restoreAll()
      }
    })

    await t.test('terminal colors are rendered as safe text, not executable server-provided HTML', async () => {
      const html = await renderToString(createSSRApp(AnsiOutput, {
        text: '\x1b[31m<script>alert("log")</script>\x1b[0m',
        label: 'Server logs'
      }))
      assert.match(html, /color:#f48771/)
      assert.match(html, /&lt;script&gt;/)
      assert.equal(html.includes('<script>'), false)
      assert.match(html, /Follow output/)
    })

    await t.test('preview regenerates after installation and ignores stale preview responses', async () => {
      setRole('viewer')
      let finishOld
      const fetch = mock.method(globalThis, 'fetch', async (url, options) => {
        if (url.endsWith('/regenerate')) {
          assert.equal(options.method, 'POST')
          return Response.json([{ id: 'working', figures: [{ id: 'plot' }] }])
        }
        return new Promise(resolve => { finishOld = resolve })
      })
      const preview = await setupComposable(() => PreviewModal.setup(
        { show: false, report: { id: 'run' } }, { expose() {}, emit() {} }
      ))
      // Setup with visible props starts a load; its older result must not overwrite regeneration.
      let visible
      await renderToString(createSSRApp({
        setup() {
          visible = PreviewModal.setup({ show: true, report: { id: 'run' } }, { expose() {}, emit() {} })
          return () => h('div')
        }
      }))
      await visible.loadPreview(true)
      finishOld(Response.json([missing]))
      await new Promise(resolve => setImmediate(resolve))
      assert.equal(visible.protocols.value[0].id, 'working')
      assert.equal(fetch.mock.calls.some(call => call.arguments[0].endsWith('/regenerate')), true)
      assert.equal(preview.protocols.value.length, 0)
      mock.restoreAll()
    })

    await t.test('report regeneration does not announce success when generation returns protocol errors', async () => {
      setRole('admin')
      mock.method(globalThis, 'fetch', async () => Response.json([missing]))
      const report = await setupComposable(() => useReportDetail(ref('run')))
      report.report.value = { id: 'run', has_cached_report: false }
      await report.handleRegenerate()
      assert.equal(report.statusBannerError.value, true)
      assert.match(report.statusBanner.value, /Qibocal is not installed/)
      assert.equal(report.statusBanner.value.includes('successfully'), false)
      assert.equal(report.report.value.has_cached_report, false)
      mock.restoreAll()
    })

    await t.test('installation completion during report loading queues regeneration until the report is ready', async () => {
      setRole('admin')
      store.state.servers = [first]
      const router = createRouter({
        history: createMemoryHistory(),
        routes: [{ path: '/reports/:id', component: { render: () => null } }]
      })
      await router.push('/reports/run')
      const previousWebSocket = globalThis.WebSocket
      let socket
      globalThis.WebSocket = class {
        constructor() { socket = this }
        close() {}
      }
      const fetch = mock.method(globalThis, 'fetch', async url => {
        assert.equal(url, `${first.url}/api/reports/run/regenerate`)
        return Response.json([missing])
      })
      const { result: report, unmount } = mountComposable(
        () => ReportView.setup({}, { emit() {}, expose() {} }),
        [router]
      )
      try {
        await new Promise(resolve => setImmediate(resolve))
        socket.onmessage({ data: JSON.stringify({ type: 'metadata', report: { id: 'run', targets: [0], platform: 'test' } }) })
        diagnostics.qibocalRevision++
        await nextTick()
        assert.equal(report.loading.value, true)
        assert.equal(fetch.mock.callCount(), 0)
        socket.onmessage({ data: JSON.stringify({ type: 'ready', protocols: [missing] }) })
        await new Promise(resolve => setImmediate(resolve))
        assert.equal(fetch.mock.callCount(), 1)
        assert.equal(report.pendingInstallationRegeneration.value, false)
      } finally {
        unmount()
        if (previousWebSocket === undefined) delete globalThis.WebSocket
        else globalThis.WebSocket = previousWebSocket
        mock.restoreAll()
      }
    })
  } finally {
    await vite.close()
    mock.restoreAll()
  }
})
