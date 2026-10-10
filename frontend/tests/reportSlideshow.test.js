import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createRenderer, h, nextTick, ref, shallowRef } from 'vue'
import { useReportSlideshow } from '../src/composables/useReportSlideshow.js'

function mount({ live = false, ids = ['first', 'second'] } = {}) {
  const protocols = ref(ids.map(id => ({ id })))
  const active = ref(live)
  const context = ref('report')
  const container = shallowRef({ scrollTop: 100 })
  const renderer = createRenderer({
    createElement: () => ({}),
    insert: () => {},
    remove: () => {},
    parentNode: () => null,
    nextSibling: () => null
  })
  let slides
  const app = renderer.createApp({
    setup() {
      slides = useReportSlideshow({
        protocols: () => protocols.value,
        live: () => active.value,
        context: () => context.value,
        container
      })
      return () => h('div')
    }
  })
  app.mount({})
  return { ...slides, protocols, active, context, container, unmount: () => app.unmount() }
}

function key(slides, name, options = {}) {
  let prevented = false
  slides.handleKeydown({
    key: name,
    preventDefault: () => { prevented = true },
    ...options
  })
  return prevented
}

test('scroll view is default; slideshow navigation includes the overview and clamps at both ends', async () => {
  const slides = mount()
  try {
    assert.equal(slides.slideshow.value, false)
    assert.equal(slides.selectedId.value, null)
    assert.equal(key(slides, 'ArrowRight'), false)
    slides.slideshow.value = true
    assert.equal(key(slides, 'ArrowLeft'), true)
    assert.equal(slides.slideIndex.value, 0)
    key(slides, 'ArrowRight')
    assert.equal(slides.selectedId.value, 'first')
    key(slides, 'ArrowRight')
    key(slides, 'ArrowRight')
    assert.equal(slides.selectedId.value, 'second')
    assert.equal(slides.slideIndex.value, 2)
    key(slides, 'ArrowUp')
    assert.equal(slides.selectedId.value, null)
    key(slides, 'ArrowDown')
    assert.equal(slides.selectedId.value, 'second')
    key(slides, 'ArrowLeft')
    assert.equal(slides.selectedId.value, 'first')
    await nextTick()
    assert.equal(slides.container.value.scrollTop, 0)
  } finally { slides.unmount() }
})

test('empty reports remain on the overview, including when the first live protocol arrives', async () => {
  const slides = mount({ live: true, ids: [] })
  try {
    slides.slideshow.value = true
    key(slides, 'ArrowDown')
    key(slides, 'ArrowRight')
    assert.equal(slides.selectedId.value, null)
    slides.protocols.value = [{ id: 'first' }]
    await nextTick()
    assert.equal(slides.selectedId.value, null)
  } finally { slides.unmount() }
})

test('Live follows appended batches only from the last protocol slide', async () => {
  for (const [live, slideshow, selectedId, expected] of [
    [true, true, 'second', 'fourth'],
    [true, true, 'first', 'first'],
    [true, true, null, null],
    [false, true, 'second', 'second'],
    [true, false, 'second', 'second']
  ]) {
    const slides = mount({ live })
    try {
      slides.slideshow.value = slideshow
      slides.selectSlide(selectedId)
      slides.protocols.value = ['first', 'second', 'third', 'fourth'].map(id => ({ id }))
      await nextTick()
      assert.equal(slides.selectedId.value, expected)
    } finally { slides.unmount() }
  }
})

test('going back suspends following and returning to the last slide resumes it', async () => {
  const slides = mount({ live: true })
  try {
    slides.slideshow.value = true
    slides.selectSlide('first')
    slides.protocols.value.push({ id: 'third' })
    await nextTick()
    assert.equal(slides.selectedId.value, 'first')
    key(slides, 'ArrowDown')
    slides.protocols.value.push({ id: 'fourth' })
    await nextTick()
    assert.equal(slides.selectedId.value, 'fourth')
  } finally { slides.unmount() }
})

test('selection survives replacements and reordering, but removals and context changes return to the overview', async () => {
  const slides = mount({ live: true })
  try {
    slides.slideshow.value = true
    slides.selectSlide('second')
    slides.protocols.value = [{ id: 'inserted' }, { id: 'second', html: 'updated' }, { id: 'first' }]
    await nextTick()
    assert.equal(slides.selectedId.value, 'second')
    assert.equal(slides.slideIndex.value, 2)
    slides.protocols.value = [{ id: 'first' }]
    await nextTick()
    assert.equal(slides.selectedId.value, null)
    slides.selectSlide('first')
    slides.context.value = 'another-report'
    assert.equal(slides.selectedId.value, null)
  } finally { slides.unmount() }
})

test('keyboard navigation leaves modifiers, editing, charts, and modal controls alone', () => {
  const slides = mount()
  try {
    slides.slideshow.value = true
    for (const options of [
      { altKey: true }, { ctrlKey: true }, { metaKey: true }, { shiftKey: true },
      { defaultPrevented: true },
      { target: { closest: selector => {
        assert.match(selector, /input.*textarea.*select.*contenteditable.*js-plotly-plot.*dialog/)
        return {}
      } } }
    ]) {
      assert.equal(key(slides, 'ArrowRight', options), false)
      assert.equal(slides.selectedId.value, null)
    }
    assert.equal(key(slides, 'Escape'), false)
  } finally { slides.unmount() }
})

test('unmount stops Live selection updates', async () => {
  const slides = mount({ live: true })
  slides.slideshow.value = true
  slides.selectSlide('second')
  slides.unmount()
  slides.protocols.value.push({ id: 'third' })
  await nextTick()
  assert.equal(slides.selectedId.value, 'second')
})
