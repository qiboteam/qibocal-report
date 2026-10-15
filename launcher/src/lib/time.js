/** Time, as people say it. Pure, and covered by `tests/time.test.js`. */

const MINUTE = 60_000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

/**
 * The distance from now, in words: "just now", "5 minutes ago", "2 days
 * ago". Coarse on purpose — this is a notification list, not a log.
 */
export function timeAgo(at, now = Date.now()) {
  const elapsed = Math.max(0, now - at)
  if (elapsed < MINUTE) return 'just now'
  const unit = (amount, name) => `${amount} ${name}${amount === 1 ? '' : 's'} ago`
  if (elapsed < HOUR) return unit(Math.floor(elapsed / MINUTE), 'minute')
  if (elapsed < DAY) return unit(Math.floor(elapsed / HOUR), 'hour')
  return unit(Math.floor(elapsed / DAY), 'day')
}

/** Whether something happened within the last day: what the bubble still shows. */
export function isRecent(at, now = Date.now()) {
  return now - at < DAY
}
