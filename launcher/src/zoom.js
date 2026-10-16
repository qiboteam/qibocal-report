/**
 * Zooming the interface, as a browser does: the command or control key
 * with `+`, `-` and `0`, the same key with the mouse wheel, and the View
 * menu. The level is the webview's, set natively, and remembered in the
 * browser's storage — the same for both pages and every window, so a new
 * window opens at the level the last one chose.
 */
import { isDesktop } from './bridge.js'
import { ZOOM_KEY, describeZoom, parseZoom, stepZoom, zoomRequest } from './lib/zoom.js'

/** How long one zoom step blocks the next: the menu's accelerator and the key may both fire. */
const DEBOUNCE_MS = 150
/** How long one wheel notch blocks the next: a trackpad sends dozens per gesture. */
const WHEEL_MS = 120

let level = parseZoom(typeof localStorage === 'undefined' ? null : localStorage.getItem(ZOOM_KEY))
let lastStep = 0
let lastWheel = 0
const listeners = new Set()

export function zoomLevel() {
  return level
}

/** Be told of every change, for a menu or a label; answers the function that stops. */
export function onZoom(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

async function apply(next) {
  level = parseZoom(next)
  try {
    localStorage.setItem(ZOOM_KEY, String(level))
  } catch {
    // A full or forbidden storage forgets the level, not the zoom.
  }
  if (isDesktop) {
    try {
      const { getCurrentWebview } = await import('@tauri-apps/api/webview')
      await getCurrentWebview().setZoom(level)
    } catch (error) {
      console.warn('The zoom could not be applied', error)
    }
  } else if (typeof document !== 'undefined') {
    // In a plain browser, for review: the page's own zoom.
    document.documentElement.style.zoom = String(level)
  }
  for (const listener of listeners) listener(level)
}

/** One step up or down; `reset` back to the default. Answers the new level. */
export async function zoom(direction) {
  const now = Date.now()
  if (now - lastStep < DEBOUNCE_MS) return level
  lastStep = now
  await apply(direction === 'reset' ? 1 : stepZoom(level, direction === 'in' ? 1 : -1))
  return level
}

export { describeZoom }

/**
 * Listen for the keys and the wheel, and apply the remembered level now.
 * Answers the function that stops listening.
 */
export function installZoom() {
  if (typeof document === 'undefined') return () => {}
  apply(level)

  function onKeydown(event) {
    const request = zoomRequest(event)
    if (!request) return
    event.preventDefault()
    zoom(request)
  }

  function onWheel(event) {
    if (!(event.ctrlKey || event.metaKey)) return
    event.preventDefault()
    const now = Date.now()
    if (now - lastWheel < WHEEL_MS || !event.deltaY) return
    lastWheel = now
    zoom(event.deltaY < 0 ? 'in' : 'out')
  }

  document.addEventListener('keydown', onKeydown)
  // Passive would forbid preventing the page's own pinch zoom.
  document.addEventListener('wheel', onWheel, { passive: false })
  return () => {
    document.removeEventListener('keydown', onKeydown)
    document.removeEventListener('wheel', onWheel)
  }
}
