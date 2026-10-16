/**
 * What the desktop launcher offers the dashboard when it embeds it.
 *
 * The launcher sets `window.qibocalDesktop` before this application mounts;
 * in a browser there is no such thing, and everything here answers that
 * nothing is there. The dashboard then falls back to its own means — a
 * toast for a message, no bell in a toolbar — and stays the same page it is
 * on the web.
 */
import { markRaw } from 'vue'
import { currentPage, pageShortcuts } from './shortcuts.js'

function desktop() {
  return typeof window !== 'undefined' ? window.qibocalDesktop : null
}

/**
 * Say something through the launcher, where everything else is said —
 * its status bar, its bell, its Notifications page — rather than as a
 * toast of this page. True when the launcher took it; false in a browser,
 * where the caller shows its toast.
 */
export function announce(message, kind = 'info') {
  const host = desktop()
  if (typeof host?.notify !== 'function') return false
  try {
    host.notify(String(message), kind)
    return true
  } catch {
    return false
  }
}

/**
 * News for the launcher to say through the system too, when nobody is
 * looking — new reports on a server. True when the launcher took it.
 */
export function alert(title, body) {
  const host = desktop()
  if (typeof host?.alert !== 'function') return false
  try {
    host.alert(String(title), String(body))
    return true
  } catch {
    return false
  }
}

/**
 * Tell the launcher which dashboard page is on screen — `dashboard`, the
 * report list; `report`, one report — so its keyboard cheatsheet lists
 * the keys of that page; null when leaving. Nothing in a browser.
 */
export function publishPage(page) {
  currentPage.value = page
  const host = desktop()
  if (typeof host?.pageShortcuts !== 'function') return
  try {
    host.pageShortcuts(page ? pageShortcuts(page) : null)
  } catch {
    // The cheatsheet is the launcher's concern, not this page's.
  }
}

/** Whether the dashboard is embedded in the desktop launcher. */
export function inDesktop() {
  return Boolean(desktop())
}

/** A launcher component to render in a toolbar — the bell — or nothing. */
export function desktopWidget(name) {
  const widget = desktop()?.widgets?.[name]
  return widget ? markRaw(widget) : null
}
