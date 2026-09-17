import { ref, onUnmounted } from 'vue'

/**
 * Composable providing reusable drag-to-resize behavior.
 * Supports horizontal (X) and vertical (Y) resizing, bounds clamping,
 * optional localStorage persistence, and automatic event cleanup.
 */
export function useResizable({
  direction = 'horizontal',
  defaultSize = 200,
  min = 50,
  max = 1000,
  storageKey = null,
  disabled = () => false
} = {}) {
  const initial = storageKey
    ? parseInt(localStorage.getItem(storageKey) || String(defaultSize), 10)
    : defaultSize

  const size = ref(Number.isNaN(initial) ? defaultSize : initial)
  const isDragging = ref(false)
  let cleanup = null

  function getMin() {
    return typeof min === 'function' ? min() : min
  }

  function getMax() {
    return typeof max === 'function' ? max() : max
  }

  function startResize(e) {
    if (typeof disabled === 'function' ? disabled() : disabled) return
    isDragging.value = true
    const startCoord = direction === 'horizontal' ? e.clientX : e.clientY
    const startSize = size.value

    const onMouseMove = (moveEvent) => {
      if (!isDragging.value) return
      const currentCoord = direction === 'horizontal' ? moveEvent.clientX : moveEvent.clientY
      const delta = currentCoord - startCoord
      const minVal = getMin()
      const maxVal = getMax()
      size.value = Math.max(minVal, Math.min(maxVal, startSize + delta))
    }

    const onMouseUp = () => {
      isDragging.value = false
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
      cleanup = null
      if (storageKey) {
        localStorage.setItem(storageKey, String(size.value))
      }
    }

    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    cleanup = onMouseUp
  }

  function reset() {
    size.value = defaultSize
    if (storageKey) {
      localStorage.setItem(storageKey, String(defaultSize))
    }
  }

  onUnmounted(() => {
    if (cleanup) cleanup()
  })

  return {
    size,
    isDragging,
    startResize,
    reset
  }
}
