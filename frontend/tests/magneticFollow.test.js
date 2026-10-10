import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createRenderer, h, nextTick, ref, shallowRef } from 'vue'
import { useMagneticFollow } from '../src/composables/useMagneticFollow.js'

function mountPanels({ live = true, cardTop = 300, cardBottom = 900, sidebarTop = 600, height = 500 } = {}) {
  const protocols = ref([{ id: 'first' }])
  const active = ref(live)
  const main = {
    scrollTop: 200, clientTop: 2, clientHeight: height,
    getBoundingClientRect: () => ({ top: 100 })
  }
  const sidebar = { scrollTop: sidebarTop, scrollHeight: 1100, clientHeight: height }
  let bounds = { top: cardTop, bottom: cardBottom }
  let renderedIds = ['first']
  const mainContainer = shallowRef(main)
  const renderer = createRenderer({
    createElement: () => ({}),
    insert: () => {},
    remove: () => {},
    parentNode: () => null,
    nextSibling: () => null
  })
  const app = renderer.createApp({
    setup() {
      useMagneticFollow({
        protocols: () => protocols.value,
        live: () => active.value,
        container: mainContainer,
        lastCard: () => renderedIds.length ? { getBoundingClientRect: () => bounds } : null
      })
      useMagneticFollow({
        protocols: () => protocols.value,
        live: () => active.value,
        container: shallowRef(sidebar)
      })
      return () => {
        const ids = protocols.value.map(protocol => protocol.id)
        if (ids.at(-1) !== renderedIds.at(-1)) {
          bounds = { top: 1200, bottom: 2000 }
          sidebar.scrollHeight = 1400
        }
        renderedIds = ids
        return h('div')
      }
    }
  })
  app.mount({})
  return {
    protocols, active, main, sidebar, mainContainer,
    setBounds: value => { bounds = value },
    unmount: () => app.unmount()
  }
}

async function update(mounted, protocols = [{ id: 'first' }, { id: 'second' }]) {
  mounted.protocols.value = protocols
  await nextTick()
  await nextTick()
}

test('Live follows the new card from a partially visible tall last card and keeps the index at the bottom', async () => {
  const mounted = mountPanels()
  try {
    await update(mounted)
    assert.equal(mounted.main.scrollTop, 1298)
    assert.equal(mounted.sidebar.scrollTop, 1400)
  } finally { mounted.unmount() }
})

test('main and index follow independently', async () => {
  for (const [options, mainTop, sidebarTop] of [
    [{ sidebarTop: 200 }, 1298, 200],
    [{ cardTop: 700, cardBottom: 1000 }, 200, 1400],
    [{ cardTop: -200, cardBottom: 102, sidebarTop: 200 }, 200, 200]
  ]) {
    const mounted = mountPanels(options)
    try {
      await update(mounted)
      assert.equal(mounted.main.scrollTop, mainTop)
      assert.equal(mounted.sidebar.scrollTop, sidebarTop)
    } finally { mounted.unmount() }
  }
})

test('returning to the last card or the index bottom resumes following', async () => {
  const mounted = mountPanels({ cardTop: 700, sidebarTop: 200 })
  try {
    await update(mounted)
    mounted.setBounds({ top: 400, bottom: 1500 })
    mounted.sidebar.scrollTop = 900
    await update(mounted, [{ id: 'first' }, { id: 'second' }, { id: 'third' }])
    assert.equal(mounted.main.scrollTop, 1298)
    assert.equal(mounted.sidebar.scrollTop, 1400)
  } finally { mounted.unmount() }
})

test('no following outside Live, for hidden panels, or for existing protocol updates and removals', async () => {
  for (const [options, protocols] of [
    [{ live: false }, [{ id: 'first' }, { id: 'second' }]],
    [{ height: 0 }, [{ id: 'first' }, { id: 'second' }]],
    [{}, [{ id: 'first', html: 'updated plot' }]],
    [{}, []],
    [{}, [{ id: 'inserted' }, { id: 'first' }]]
  ]) {
    const mounted = mountPanels(options)
    try {
      await update(mounted, protocols)
      assert.equal(mounted.main.scrollTop, 200)
      assert.equal(mounted.sidebar.scrollTop, 600)
    } finally { mounted.unmount() }
  }
})

test('index bottom tolerates fractional scroll positions but not scrolling away', async () => {
  for (const [sidebarTop, expected] of [[599.5, 1400], [598, 598]]) {
    const mounted = mountPanels({ sidebarTop })
    try {
      await update(mounted)
      assert.equal(mounted.sidebar.scrollTop, expected)
    } finally { mounted.unmount() }
  }
})

test('batched new protocols follow the last card only', async () => {
  const mounted = mountPanels()
  try {
    await update(mounted, [{ id: 'first' }, { id: 'second' }, { id: 'third' }])
    assert.equal(mounted.main.scrollTop, 1298)
    assert.equal(mounted.sidebar.scrollTop, 1400)
  } finally { mounted.unmount() }
})

test('stopping Live, replacing the panel, or unmounting cancels pending follow', async () => {
  for (const cancel of [
    mounted => { mounted.active.value = false },
    mounted => { mounted.active.value = false; mounted.active.value = true },
    mounted => { mounted.mainContainer.value = null; mounted.active.value = false },
    mounted => mounted.unmount()
  ]) {
    const mounted = mountPanels()
    try {
      mounted.protocols.value = [{ id: 'first' }, { id: 'second' }]
      await nextTick()
      cancel(mounted)
      await nextTick()
      assert.equal(mounted.main.scrollTop, 200)
      assert.equal(mounted.sidebar.scrollTop, 600)
    } finally { mounted.unmount() }
  }
})
