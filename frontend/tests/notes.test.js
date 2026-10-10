import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { readFile } from 'node:fs/promises'
import { createServer } from 'vite'
import vue from '@vitejs/plugin-vue'
import { parse, compileScript } from 'vue/compiler-sfc'
import { createRenderer, createSSRApp, h, reactive, nextTick } from 'vue'
import { renderToString } from 'vue/server-renderer'

test('append-only report and protocol comments', async t => {
  globalThis.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} }
  globalThis.sessionStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} }
  const originalFetch = globalThis.fetch
  const originalDocument = globalThis.document
  const originalDocumentClass = globalThis.Document
  const originalShadowRoot = globalThis.ShadowRoot
  const panelSource = await readFile(new URL('../src/components/report/NotesPanel.vue', import.meta.url), 'utf8')
  const clientModuleId = fileURLToPath(new URL('../src/components/report/NotesPanel.client-test.js', import.meta.url))
  const vite = await createServer({
    configFile: false,
    root: fileURLToPath(new URL('..', import.meta.url)),
    plugins: [
      {
        name: 'notes-client-test',
        resolveId: id => id === '/notes-panel-client-test' ? clientModuleId : null,
        load: id => id === clientModuleId
          ? compileScript(parse(panelSource).descriptor, { id: 'notes-client-test', inlineTemplate: true }).content
          : null
      },
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
    const { useNotes, normalizeNotes } = await vite.ssrLoadModule('/src/composables/useNotes.js')
    const { default: NotesPanel } = await vite.ssrLoadModule('/src/components/report/NotesPanel.vue')
    const { default: ProtocolCard } = await vite.ssrLoadModule('/src/components/report/ProtocolCard.vue')
    const { default: ClientNotesPanel } = await vite.ssrLoadModule('/notes-panel-client-test')
    const server = { id: 'first', url: 'https://first.example' }
    const note = { content: 'First\ncomment', timestamp: '2026-10-10T06:00:00Z', author: null }
    function reset(role = null) {
      store.state.activeServer = { ...server }
      store.state.auth.enabled = role !== null
      store.setServerAuth(server, role ? 'session-token' : null,
        role ? { id: 'user', username: 'alice', role } : null)
    }
    function mount(overrides = {}) {
      const props = reactive({ reportId: 'folder/run #1', protocolId: null, notes: [], ...overrides })
      const events = []
      let panel
      const renderer = createRenderer({
        createComment: text => ({ text }),
        insert: (node, parent) => { parent.node = node },
        remove: () => {},
        parentNode: () => null,
        nextSibling: () => null
      })
      const app = renderer.createApp({
        setup() {
          panel = useNotes(props, (name, history) => {
            events.push({ name, history })
            props.notes = history
          })
          return () => null
        }
      })
      app.mount({})
      return { panel, props, events, unmount: () => app.unmount() }
    }

    await t.test('missing and malformed legacy histories are safe', async () => {
      reset()
      for (const value of [undefined, null, '', {}, [null, { content: 5 }]]) {
        assert.deepEqual(normalizeNotes(value), [])
      }
      const html = await renderToString(createSSRApp(NotesPanel, { reportId: 'run' }))
      assert.match(html, /No comments yet/)
      assert.match(html, /Add a comment/)
      assert.match(html, /cannot be edited or deleted/)
    })

    await t.test('history renders escaped plain text, whitespace, time and optional author', async () => {
      reset('viewer')
      const html = await renderToString(createSSRApp(NotesPanel, {
        reportId: 'run',
        notes: [note, { ...note, author: '<alice>', content: '<script>alert(1)</script>\n line' }]
      }))
      assert.match(html, /whitespace-pre-wrap/)
      assert.match(html, /<time datetime="2026-10-10T06:00:00Z"/)
      assert.match(html, /&lt;alice&gt;/)
      assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;\n line/)
      assert.doesNotMatch(html, /<form|<textarea|<script>/)
      store.state.auth.user = null
      const loggedOut = await renderToString(createSSRApp(NotesPanel, { reportId: 'run' }))
      assert.doesNotMatch(loggedOut, /<form/)
    })

    await t.test('actual Vue toggle, form, errors, permission and navigation lifecycle', async subtest => {
      reset('editor')
      globalThis.document = { activeElement: null }
      globalThis.Document = class {}
      globalThis.ShadowRoot = class {}
      function node(tag, text = '') {
        return {
          tag, tagName: tag.toUpperCase(), text, children: [], props: {}, listeners: {},
          getRootNode: () => globalThis.document,
          addEventListener(name, callback) { this.listeners[name] = callback },
          removeEventListener(name) { delete this.listeners[name] }
        }
      }
      const renderer = createRenderer({
        createElement: tag => node(tag),
        createText: text => node('#text', text),
        createComment: text => node('#comment', text),
        setText: (element, text) => { element.text = text },
        setElementText: (element, text) => { element.text = text; element.children = [] },
        patchProp: (element, name, previous, value) => { element.props[name] = value },
        insert(element, parent, anchor = null) {
          if (element.parent) element.parent.children.splice(element.parent.children.indexOf(element), 1)
          const index = parent.children.indexOf(anchor)
          parent.children.splice(index < 0 ? parent.children.length : index, 0, element)
          element.parent = parent
        },
        remove(element) { element.parent.children.splice(element.parent.children.indexOf(element), 1) },
        parentNode: element => element.parent,
        nextSibling: element => element.parent?.children[element.parent.children.indexOf(element) + 1]
      })
      const props = reactive({ reportId: 'run', notes: [note] })
      const root = node('root')
      const app = renderer.createApp({
        render: () => h(ClientNotesPanel, {
          ...props, 'onUpdate:notes': history => { props.notes = history }
        })
      })
      app.mount(root)
      subtest.after(() => app.unmount())
      const all = element => [element, ...element.children.flatMap(all)]
      const find = tag => all(root).find(element => element.tag === tag)
      const text = element => element.text + element.children.map(text).join('')
      const input = value => {
        const textarea = find('textarea')
        textarea.value = value
        textarea.listeners.input({ target: textarea })
      }
      const settle = async () => {
        for (let i = 0; i < 8; i++) await new Promise(resolve => setImmediate(resolve))
        await nextTick()
      }
      let calls = 0
      globalThis.fetch = async () => { calls++; return Response.json([note]) }
      assert.equal(calls, 0)
      assert.ok(find('summary'))
      assert.ok(find('form'))
      find('details').props.onToggle({ target: { open: true } })
      await settle()
      assert.equal(calls, 1)
      assert.equal(find('time').props.datetime, note.timestamp)
      assert.match(text(root), /First\ncomment/)

      input('Keep my draft')
      globalThis.fetch = async () => Response.json({ detail: 'Protocol not found' }, { status: 404 })
      find('form').props.onSubmit({ preventDefault() {} })
      await settle()
      assert.match(text(root), /Protocol not found/)
      assert.equal(find('textarea').value, 'Keep my draft')
      globalThis.fetch = async () => Response.json([note, { ...note, content: 'Keep my draft' }])
      find('form').props.onSubmit({ preventDefault() {} })
      await settle()
      assert.equal(props.notes.length, 2)
      assert.equal(find('textarea').value, '')
      assert.doesNotMatch(text(root), /Protocol not found/)

      let resolveOld
      let resolveNew
      globalThis.fetch = url => new Promise(resolve => {
        if (url.endsWith('/run/notes')) resolveOld = resolve
        else resolveNew = resolve
      })
      input('Wrong report draft')
      find('form').props.onSubmit({ preventDefault() {} })
      await nextTick()
      assert.equal(find('textarea').props.disabled, true)
      props.reportId = 'next-run'
      props.notes = []
      await nextTick()
      assert.equal(find('textarea').value, '')
      resolveOld(Response.json([{ ...note, content: 'Stale navigation result' }]))
      resolveNew(Response.json([]))
      await settle()
      assert.doesNotMatch(text(root), /Stale navigation result/)
      assert.deepEqual(props.notes, [])

      globalThis.fetch = () => new Promise(resolve => { resolveOld = resolve })
      input('Wrong identity draft')
      find('form').props.onSubmit({ preventDefault() {} })
      await nextTick()
      globalThis.fetch = async () => Response.json([])
      store.setServerAuth(server, 'changed-session', { id: 'new-user', username: 'bob', role: 'editor' })
      await settle()
      assert.equal(find('textarea').value, '')
      resolveOld(Response.json([{ ...note, content: 'Stale identity result' }]))
      await settle()
      assert.doesNotMatch(text(root), /Stale identity result/)
      store.state.auth.user.role = 'viewer'
      await settle()
      assert.equal(find('form'), undefined)
      assert.equal(find('textarea'), undefined)
      app.unmount()
    })

    await t.test('GET and append POST encode both IDs, retain auth and accept server history', async () => {
      for (const role of [null, 'editor', 'admin']) {
        reset(role)
        const { panel, events, unmount } = mount({ protocolId: 'rabi/q0 #1', notes: [note] })
        const requests = []
        const updated = [note, { ...note, content: 'New\n comment', author: role ? 'alice' : null }]
        globalThis.fetch = async (url, options) => {
          requests.push({ url, options })
          assert.equal(url, 'https://first.example/api/reports/folder%2Frun%20%231/protocols/rabi%2Fq0%20%231/notes')
          assert.equal(options.headers.get('Authorization'), role ? 'Bearer session-token' : null)
          return Response.json(options.method === 'POST' ? updated : [note])
        }
        await panel.loadNotes()
        assert.equal(requests[0].options.cache, 'no-store')
        panel.draft.value = 'New\n comment'
        await panel.addComment()
        assert.equal(requests[1].options.method, 'POST')
        assert.deepEqual(JSON.parse(requests[1].options.body), { content: 'New\n comment' })
        assert.deepEqual(panel.notes.value, updated)
        assert.equal(panel.draft.value, '')
        assert.equal(events.at(-1).name, 'update:notes')
        unmount()
      }
    })

    await t.test('session endpoint, permission checks, blank drafts and failure preservation', async () => {
      reset('viewer')
      const { panel, unmount } = mount({ notes: [note] })
      let calls = 0
      globalThis.fetch = async (url, options) => {
        calls++
        assert.equal(url, 'https://first.example/api/reports/folder%2Frun%20%231/notes')
        assert.equal(options.method, 'POST')
        return Response.json({ detail: 'Not allowed' }, { status: 403 })
      }
      panel.draft.value = 'Keep this draft'
      await panel.addComment()
      assert.equal(calls, 0)
      store.state.auth.user.role = 'editor'
      panel.draft.value = ' \n '
      await panel.addComment()
      assert.equal(calls, 0)
      panel.draft.value = 'Keep this draft'
      await panel.addComment()
      assert.equal(panel.error.value, 'Not allowed')
      assert.equal(panel.draft.value, 'Keep this draft')
      assert.deepEqual(panel.notes.value, [])
      globalThis.fetch = async () => { throw new Error('Offline') }
      await panel.addComment()
      assert.equal(panel.error.value, 'Offline')
      assert.equal(panel.draft.value, 'Keep this draft')
      globalThis.fetch = async () => Response.json({ detail: 'Unavailable' }, { status: 500 })
      await panel.loadNotes()
      assert.equal(panel.error.value, 'Unavailable')
      assert.equal(panel.draft.value, 'Keep this draft')
      globalThis.fetch = async () => Response.json([note, { ...note, content: 'Keep this draft' }])
      await panel.addComment()
      assert.equal(panel.error.value, '')
      assert.equal(panel.draft.value, '')
      assert.equal(panel.notes.value.length, 2)
      unmount()
    })

    await t.test('duplicate submissions are blocked and invalid histories preserve drafts', async () => {
      reset()
      const { panel, events, unmount } = mount({ notes: [note] })
      let resolve
      let calls = 0
      globalThis.fetch = () => {
        calls++
        return new Promise(done => { resolve = done })
      }
      panel.draft.value = 'Pending'
      const pending = panel.addComment()
      await panel.addComment()
      assert.equal(calls, 1)
      assert.equal(panel.saving.value, true)
      resolve(Response.json({ notes: [] }))
      await pending
      assert.equal(panel.error.value, 'Invalid notes history returned by server')
      assert.equal(panel.draft.value, 'Pending')
      assert.deepEqual(panel.notes.value, [note])
      assert.equal(events.length, 0)
      assert.equal(panel.saving.value, false)
      unmount()
    })

    await t.test('malformed server history rows fail without discarding existing notes or drafts', async () => {
      for (const method of ['GET', 'POST']) {
        for (const malformed of [
          null,
          {},
          { content: 42, timestamp: note.timestamp },
          { content: 'Missing timestamp' },
          { content: 'Bad timestamp', timestamp: 42 },
          { ...note, author: 42 }
        ]) {
          reset()
          const { panel, events, unmount } = mount({ notes: [note] })
          panel.draft.value = 'Preserve my draft'
          globalThis.fetch = async () => Response.json([note, malformed])
          await (method === 'POST' ? panel.addComment() : panel.loadNotes())
          assert.equal(panel.error.value, 'Invalid notes history returned by server')
          assert.deepEqual(panel.notes.value, [note])
          assert.equal(panel.draft.value, 'Preserve my draft')
          assert.equal(events.length, 0)
          assert.equal(panel.loading.value, false)
          assert.equal(panel.saving.value, false)
          unmount()
        }
      }
      reset()
      const { panel, unmount } = mount()
      const withoutAuthor = { content: 'Optional author', timestamp: note.timestamp }
      globalThis.fetch = async () => Response.json([withoutAuthor])
      await panel.loadNotes()
      assert.equal(panel.error.value, '')
      assert.deepEqual(panel.notes.value, [withoutAuthor])
      unmount()
    })

    await t.test('a late POST retains newer streamed history and refreshes after saving ends', async () => {
      reset()
      const { panel, props, events, unmount } = mount({ notes: [note] })
      const added = { ...note, content: 'My comment' }
      const streamed = [note, added, { ...note, content: 'Newer streamed comment' }]
      const fresh = [...streamed, { ...note, content: 'Latest comment' }]
      let resolvePost
      let resolveGet
      let reads = 0
      globalThis.fetch = (url, options) => {
        if (options.method === 'POST') return new Promise(resolve => { resolvePost = resolve })
        reads++
        assert.equal(panel.saving.value, false)
        assert.equal(options.cache, 'no-store')
        return new Promise(resolve => { resolveGet = resolve })
      }
      panel.draft.value = 'My comment'
      const pending = panel.addComment()
      props.notes = streamed
      resolvePost(Response.json([note, added]))
      for (let i = 0; i < 8 && !resolveGet; i++) await new Promise(resolve => setImmediate(resolve))
      assert.equal(reads, 1)
      assert.deepEqual(panel.notes.value, streamed)
      assert.equal(events.length, 0)
      assert.equal(panel.draft.value, '')
      assert.equal(panel.loading.value, true)
      resolveGet(Response.json(fresh))
      await pending
      assert.deepEqual(panel.notes.value, fresh)
      assert.equal(events.length, 1)
      assert.deepEqual(events[0].history, fresh)
      assert.equal(panel.loading.value, false)
      unmount()
    })

    await t.test('superseded POST refresh failures retain the stream and navigation skips refresh', async () => {
      for (const navigate of [false, true]) {
        reset()
        const { panel, props, events, unmount } = mount({ notes: [note] })
        const streamed = [note, { ...note, content: 'Newer streamed comment' }]
        let resolvePost
        let reads = 0
        globalThis.fetch = (url, options) => {
          if (options.method === 'POST') return new Promise(resolve => { resolvePost = resolve })
          reads++
          return Promise.resolve(Response.json({ detail: 'Refresh unavailable' }, { status: 503 }))
        }
        panel.draft.value = 'Posted comment'
        const pending = panel.addComment()
        props.notes = streamed
        if (navigate) props.reportId = 'new-report'
        resolvePost(Response.json([note]))
        await pending
        assert.equal(reads, navigate ? 0 : 1)
        assert.equal(events.length, 0)
        assert.deepEqual(panel.notes.value, navigate ? [] : streamed)
        assert.equal(panel.error.value, navigate ? '' : 'Refresh unavailable')
        assert.equal(panel.saving.value, false)
        assert.equal(panel.loading.value, false)
        unmount()
      }
    })

    await t.test('report, protocol, server, identity changes and unmount reject late GET/POST results', async () => {
      for (const method of ['GET', 'POST']) {
        for (const change of [
          ({ props }) => { props.reportId = 'other' },
          ({ props }) => { props.protocolId = 'other-protocol' },
          () => { store.state.activeServer.url = 'https://other.example' },
          () => { store.state.activeServer.id = 'other-server' },
          () => { store.setServerAuth(server, 'replacement-token', { id: 'other', role: 'editor' }) },
          () => { store.state.auth.user.role = 'viewer' },
          ({ unmount }) => unmount()
        ]) {
          reset('editor')
          const mounted = mount()
          let resolve
          let requestedUrl
          globalThis.fetch = url => {
            requestedUrl = url
            return new Promise(done => { resolve = done })
          }
          mounted.panel.draft.value = 'Old draft'
          const pending = method === 'POST' ? mounted.panel.addComment() : mounted.panel.loadNotes()
          change(mounted)
          resolve(Response.json([note]))
          await pending
          assert.equal(requestedUrl, 'https://first.example/api/reports/folder%2Frun%20%231/notes')
          assert.equal(mounted.events.length, 0)
          assert.deepEqual(mounted.panel.notes.value, [])
          mounted.unmount()
        }
      }
    })

    await t.test('streams supersede GET and POST supersedes an older GET', async () => {
      reset()
      const { panel, props, unmount } = mount()
      let resolveGet
      globalThis.fetch = async (url, options) => options.method === 'POST'
        ? Response.json([note, { ...note, content: 'Added' }])
        : new Promise(resolve => { resolveGet = resolve })
      const first = panel.loadNotes()
      props.notes = [note]
      resolveGet(Response.json([]))
      await first
      assert.deepEqual(panel.notes.value, [note])
      const second = panel.loadNotes()
      panel.draft.value = 'Added'
      await panel.addComment()
      resolveGet(Response.json([]))
      await second
      assert.equal(panel.notes.value.length, 2)
      unmount()
    })

    await t.test('protocol histories remain available for cached, empty and failed plot results', async () => {
      reset('viewer')
      for (const output of [{ cached: true, html: '<p>Cached</p>' }, {}, { error: 'Plot unavailable', status: 'error' }]) {
        const html = await renderToString(createSSRApp({
          render: () => h(ProtocolCard, {
            reportId: 'run', index: 0,
            proto: { id: 'rabi', name: 'Rabi', figures: [], notes: [note], ...output }
          })
        }))
        assert.match(html, /Protocol comments/)
        assert.match(html, /First\ncomment/)
      }
    })
  } finally {
    globalThis.fetch = originalFetch
    globalThis.document = originalDocument
    globalThis.Document = originalDocumentClass
    globalThis.ShadowRoot = originalShadowRoot
    await vite.close()
  }
})
