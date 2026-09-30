import assert from 'node:assert/strict'
import { test, mock } from 'node:test'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createSSRApp, h, ref } from 'vue'
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
    const { default: QibocalControls } = await vite.ssrLoadModule('/src/components/report/QibocalControls.vue')
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
        const html = await renderToString(createSSRApp(QibocalControls, { missing: true }))
        assert.equal(html.includes('Install Qibocal'), expected)
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
      assert.match(html, /Install Qibocal/)
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
        assert.equal(html.includes('Install Qibocal'), role === 'admin')
        mock.restoreAll()
      }
    })

    await t.test('picker shows recent versions and Git and regenerates after installing a selected version', async () => {
      setRole('admin')
      const installed = mock.fn()
      mock.method(globalThis, 'fetch', async (url, options) => {
        if (url.endsWith('/api/qibocal')) return Response.json({ installed: true, version: '0.2.4', source: 'pypi' })
        if (url.endsWith('/options')) return Response.json(choices)
        assert.equal(url, `${first.url}/api/admin/qibocal/install`)
        assert.equal(options.headers.get('Authorization'), 'Bearer admin-session')
        assert.deepEqual(JSON.parse(options.body), { option: 'pypi:0.2.5' })
        return Response.json({ installed: true, version: '0.2.5', source: 'pypi' })
      })
      const environment = await setupComposable(() => useQibocalEnvironment(installed))
      await environment.open()
      assert.deepEqual(environment.options.value.map(option => option.id), ['pypi:0.2.5', 'git'])
      assert.equal(environment.selected.value, 'pypi:0.2.5')
      await environment.install()
      assert.equal(environment.show.value, false)
      assert.equal(environment.environment.value.version, '0.2.5')
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
      await environment.open()
      assert.equal(environment.pypiError.value, 'PyPI is unavailable.')
      assert.equal(environment.selected.value, 'git')
      await environment.install()
      assert.equal(environment.show.value, true)
      assert.equal(environment.error.value, 'Server environment is read-only.')
      assert.equal(installed.mock.callCount(), 0)
      mock.restoreAll()
    })

    await t.test('the switch-version dialog displays the current version and both installation sources', async () => {
      setRole('admin')
      mock.method(globalThis, 'fetch', async url => Response.json(url.endsWith('/options')
        ? { ...choices, installed: true, version: '0.2.4', source: 'pypi' }
        : { installed: true, version: '0.2.4', source: 'pypi' }))
      const context = {}
      const html = await renderToString(createSSRApp({
        ...QibocalControls,
        async setup(props, setupContext) {
          const controls = QibocalControls.setup(props, setupContext)
          await controls.open()
          return controls
        }
      }), context)
      assert.match(html, /Switch Qibocal Version/)
      assert.match(context.teleports.body, /Current version:.*0\.2\.4/)
      assert.match(context.teleports.body, /Qibocal 0\.2\.5 \(PyPI\)/)
      assert.match(context.teleports.body, /Git repository \(latest\)/)
      assert.match(context.teleports.body, /Install and Regenerate/)
      assert.match(context.teleports.body, /for all users/)
      mock.restoreAll()
    })

    await t.test('installation cannot be duplicated or dismissed while pending, and old server results are ignored', async () => {
      setRole('admin')
      let finishInstall
      const installed = mock.fn()
      const fetch = mock.method(globalThis, 'fetch', async url => {
        if (url.endsWith('/api/qibocal')) return Response.json({ installed: false })
        if (url.endsWith('/options')) return Response.json(choices)
        return new Promise(resolve => { finishInstall = resolve })
      })
      const environment = await setupComposable(() => useQibocalEnvironment(installed))
      await environment.open()
      const pending = environment.install()
      await environment.install()
      environment.close()
      assert.equal(environment.show.value, true)
      assert.equal(fetch.mock.calls.filter(call => call.arguments[0].endsWith('/install')).length, 1)
      store.state.activeServer = second
      finishInstall(Response.json({ installed: true, version: '0.2.5', source: 'pypi' }))
      await pending
      assert.equal(installed.mock.callCount(), 0)
      assert.equal(environment.environment.value.installed, false)
      mock.restoreAll()
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
  } finally {
    await vite.close()
    mock.restoreAll()
  }
})
