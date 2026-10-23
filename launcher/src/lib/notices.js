/**
 * The notifications, kept across the two pages of the window.
 *
 * The launcher page and the dashboard page are separate documents: what
 * one says would be lost when the other loads, were it kept in memory
 * alone. Session storage belongs to the window and outlives a navigation
 * within it, not the application: exactly "since it was opened". Pure, and
 * covered by `tests/notices.test.js`.
 */

export const NOTICES_KEY = 'qibocamp_launcher_notices'

/** How many notifications are kept, newest first. */
export const NOTICE_LIMIT = 50

/** The notifications a storage holds; nothing when it holds nonsense. */
export function loadNotices(storage) {
  try {
    const parsed = JSON.parse(storage?.getItem(NOTICES_KEY) || '[]')
    if (!Array.isArray(parsed)) return []
    return parsed
      .filter(entry => entry && typeof entry === 'object' && typeof entry.text === 'string' && Number.isFinite(entry.at))
      .map(entry => ({
        id: Number.isInteger(entry.id) ? entry.id : 0,
        text: entry.text,
        kind: entry.kind === 'error' ? 'error' : 'info',
        at: entry.at,
        link: entry.link && typeof entry.link === 'object' ? entry.link : null,
        archived: Boolean(entry.archived)
      }))
      .slice(0, NOTICE_LIMIT)
  } catch {
    return []
  }
}

export function storeNotices(storage, notices) {
  try {
    storage?.setItem(NOTICES_KEY, JSON.stringify(notices.slice(0, NOTICE_LIMIT)))
  } catch {
    // A full or forbidden storage loses the history, not the application.
  }
}

/** The identifier after the ones in use. */
export function nextNoticeId(notices) {
  return notices.reduce((highest, entry) => Math.max(highest, entry.id || 0), 0) + 1
}
