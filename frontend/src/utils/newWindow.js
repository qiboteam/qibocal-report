/**
 * Opening a page in a new window — or, in a browser, a new tab — the way
 * links do everywhere: a modifier held, the middle button, Shift+Enter.
 * Inside the desktop launcher `window.open` is answered with a window of
 * the application for its own pages, so the same gesture works there.
 */

/** Whether a click, or a key, asks for a new window. */
export function wantsNewWindow(event) {
  return Boolean(event && (event.metaKey || event.ctrlKey || event.shiftKey || event.button === 1))
}

/**
 * Show a native context menu with `items` of `{ text, action }` — or
 * `{ separator: true }` — where the application provides one, in place of
 * the webview's own; false in a browser, whose menu knows the links.
 */
export function showContextMenu(event, items) {
  const host = typeof window !== 'undefined' ? window.qibocampDesktop : null
  if (typeof host?.contextMenu !== 'function') return false
  event.preventDefault()
  Promise.resolve(host.contextMenu({ items })).catch(error => console.warn('The context menu could not be shown', error))
  return true
}

/** Open an address of this application in a new window or tab. */
export function openInNewWindow(href) {
  if (typeof window === 'undefined') return
  const target = new URL(href, window.location.href).href
  window.open(target, '_blank', 'noopener')
}
