import { computed, nextTick, ref, watch } from 'vue'

/**
 * The protocol an address names, `?protocol=`: by id, or by name as a search
 * result links it; null for the overview, or one the report does not hold.
 */
export function slideFromQuery(value, list = []) {
  if (value === undefined || value === null || value === '') return null
  const clean = String(value).toLowerCase().trim()
  const matched = list.find(protocol => protocol.id?.toLowerCase() === clean || protocol.name?.toLowerCase() === clean)
  return matched?.id ?? null
}

/**
 * One protocol at a time, or the whole report. With `navigate(id, { replace })`,
 * a slide is a page of its own: shown at once, and named in the address, so
 * the browser's history goes back to the previous slide; `showSlide` shows
 * the one the address names, after Back or Forward. What happens without
 * the user, Live following or a protocol leaving, replaces the address
 * instead.
 */
export function useReportSlideshow({ protocols, live, context, container, navigate = null }) {
  // One protocol at a time is the default; the whole report scrolls on request.
  const slideshow = ref(true)
  const selectedId = ref(null)
  const slideIndex = computed(() => {
    const index = protocols().findIndex(protocol => protocol.id === selectedId.value)
    return index + 1
  })

  /** Show a slide, or place the cursor of the continuous view. */
  function showSlide(id) {
    selectedId.value = id
    if (slideshow.value) {
      nextTick(() => {
        if (container.value) container.value.scrollTop = 0
      })
    }
  }

  /** Go to a slide: through the address when the slideshow has one. */
  function selectSlide(id, { replace = false } = {}) {
    if (navigate && slideshow.value) navigate(id, { replace })
    showSlide(id)
  }

  function moveSlide(delta) {
    const index = Math.max(0, Math.min(protocols().length, slideIndex.value + delta))
    selectSlide(index === 0 ? null : protocols()[index - 1].id)
  }

  function handleKeydown(event) {
    if (!slideshow.value || event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return
    // Leave text editing, chart interactions, and modal controls to their owners.
    if (event.target?.closest('input, textarea, select, [contenteditable]:not([contenteditable="false"]), .js-plotly-plot, [role="dialog"], .fixed')) return
    switch (event.key) {
      case 'ArrowLeft': moveSlide(-1); break
      case 'ArrowRight': moveSlide(1); break
      case 'ArrowUp': selectSlide(null); break
      case 'ArrowDown': selectSlide(protocols().at(-1)?.id ?? null); break
      default: return
    }
    event.preventDefault()
  }

  watch(
    () => protocols().map(protocol => protocol.id),
    (ids, previousIds) => {
      const lastId = ids.at(-1)
      if (slideshow.value && live() && selectedId.value !== null &&
          selectedId.value === previousIds.at(-1) && lastId !== undefined && !previousIds.includes(lastId)) {
        selectSlide(lastId, { replace: true })
      } else if (selectedId.value !== null && !ids.includes(selectedId.value)) {
        selectSlide(null, { replace: true })
      }
    }
  )

  watch(context, () => { selectedId.value = null }, { flush: 'sync' })

  return { slideshow, selectedId, slideIndex, showSlide, selectSlide, moveSlide, handleKeydown }
}
