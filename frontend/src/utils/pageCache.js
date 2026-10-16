/**
 * The pages of reports last shown, kept for a little while.
 *
 * The cache lives outside any component, so a round trip to a report and
 * back within its lifetime shows the list at once — the same server, the
 * same filters, the same page — instead of asking the server again for what
 * it just answered. Pure, and covered by `tests/pageCache.test.js`.
 */

/** How long a page is trusted once fetched. */
export const PAGE_CACHE_TTL_MS = 10_000

const pages = new Map()

export function pageCacheKey(queryKey, page) {
  return `${queryKey}|p_${page}`
}

function fresh(entry, now) {
  return Boolean(entry) && now - entry.at < PAGE_CACHE_TTL_MS
}

export function readPage(key, now = Date.now()) {
  const entry = pages.get(key)
  if (!fresh(entry, now)) {
    pages.delete(key)
    return undefined
  }
  return entry.data
}

export function hasPage(key, now = Date.now()) {
  return fresh(pages.get(key), now)
}

export function writePage(key, data, now = Date.now()) {
  pages.set(key, { data, at: now })
}

export function clearPages() {
  pages.clear()
}
