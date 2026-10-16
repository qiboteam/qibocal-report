/**
 * When something deserves a system notification: the user is not looking.
 * Pure, and covered by `tests/alerts.test.js`; asking the system is the
 * bridge's business.
 */

/**
 * Whether the user is away from `page` — the hash path where the news
 * would be seen, such as `/processes` — because the window is hidden or
 * behind another, or because another page is on screen. Without a page,
 * only the window counts.
 */
export function unattended({ hidden = false, focused = true, hash = '', page = null } = {}) {
  if (hidden || !focused) return true
  if (!page) return false
  const path = String(hash || '').replace(/^#/, '').split('?')[0]
  return path !== page && !path.startsWith(`${page}/`)
}

/** What a process's change of state says, or null when it says nothing. */
export function processNews(previous, info) {
  if (!info || info.kind === 'setup' || info.kind === 'update') return null
  const label = info.label || info.kind
  const wasUp = Boolean(previous?.url) && previous?.status === 'running'
  if (info.status === 'running' && info.url && !wasUp) {
    return { title: `${label} is up`, body: `${label} answers at ${info.url}.` }
  }
  if (info.status === 'failed' && previous?.status !== 'failed') {
    return { title: `${label} failed`, body: `${label} stopped with an error; its output is in Running.` }
  }
  return null
}
