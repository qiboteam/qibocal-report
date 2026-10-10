import { computed, nextTick, ref, watch } from 'vue'

export function useReportSlideshow({ protocols, live, context, container }) {
  const slideshow = ref(false)
  const selectedId = ref(null)
  const slideIndex = computed(() => {
    const index = protocols().findIndex(protocol => protocol.id === selectedId.value)
    return index + 1
  })

  function selectSlide(id) {
    selectedId.value = id
    if (slideshow.value) {
      nextTick(() => {
        if (container.value) container.value.scrollTop = 0
      })
    }
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
        selectSlide(lastId)
      } else if (selectedId.value !== null && !ids.includes(selectedId.value)) {
        selectSlide(null)
      }
    }
  )

  watch(context, () => { selectedId.value = null }, { flush: 'sync' })

  return { slideshow, selectedId, slideIndex, selectSlide, moveSlide, handleKeydown }
}
