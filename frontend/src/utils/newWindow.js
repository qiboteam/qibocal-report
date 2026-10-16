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

/** Open an address of this application in a new window or tab. */
export function openInNewWindow(href) {
  if (typeof window === 'undefined') return
  const target = new URL(href, window.location.href).href
  window.open(target, '_blank', 'noopener')
}
