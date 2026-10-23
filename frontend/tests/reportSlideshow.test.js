import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createRenderer, h, nextTick, ref, shallowRef } from 'vue'
import { slideFromQuery, useReportSlideshow } from '../src/composables/useReportSlideshow.js'

function mount({ live = false, ids = ['first', 'second'], navigate = null } = {}) {
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
        container,
        navigate
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

test('the slideshow is the default view; its navigation includes the overview and clamps at both ends', async () => {
  const slides = mount()
  try {
    assert.equal(slides.slideshow.value, true)
    assert.equal(slides.selectedId.value, null)
    slides.slideshow.value = false
    assert.equal(key(slides, 'ArrowRight'), false, 'the keys belong to the slideshow alone')
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

test('an address names a slide by id, or by name as a search links it', () => {
  const list = [{ id: 'rabi-0', name: 'Rabi' }, { id: 'ramsey-0', name: 'Ramsey' }]
  assert.equal(slideFromQuery('ramsey-0', list), 'ramsey-0')
  assert.equal(slideFromQuery(' RABI ', list), 'rabi-0')
  assert.equal(slideFromQuery(undefined, list), null)
  assert.equal(slideFromQuery('', list), null)
  assert.equal(slideFromQuery('t1-0', list), null, 'one the report does not hold is the overview')
})

test('with an address, the slideshow pushes the slides the user picks and replaces the ones it follows', async () => {
  const visits = []
  const slides = mount({ live: true, navigate: (id, { replace }) => visits.push([id, replace]) })
  try {
    slides.selectSlide('first')
    key(slides, 'ArrowRight')
    key(slides, 'ArrowUp')
    assert.deepEqual(visits, [['first', false], ['second', false], [null, false]])
    assert.equal(slides.selectedId.value, null, 'shown at once, before the address names it')
    key(slides, 'ArrowDown')
    visits.length = 0
    slides.protocols.value = ['first', 'second', 'third'].map(id => ({ id }))
    await nextTick()
    assert.deepEqual(visits, [['third', true]], 'Live following adds no page to the history')
    slides.protocols.value = [{ id: 'first' }]
    await nextTick()
    assert.deepEqual(visits.at(-1), [null, true])
    visits.length = 0
    slides.slideshow.value = false
    slides.selectSlide('first')
    assert.deepEqual(visits, [], 'the continuous view keeps the address')
    slides.slideshow.value = true
    slides.showSlide('first')
    assert.deepEqual(visits, [], 'Back and Forward show a slide without asking for it again')
    assert.equal(slides.selectedId.value, 'first')
  } finally { slides.unmount() }
})
