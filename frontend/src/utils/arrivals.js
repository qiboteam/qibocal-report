/**
 * New reports on a server: the count seen last time against the count now.
 * The first sight of a server counts nothing; a count that fell — reports
 * deleted — counts nothing either. Pure, and covered by `tests/arrivals.test.js`.
 */
export function createArrivals() {
  const seen = new Map()
  return function arrivals(key, count) {
    if (!Number.isFinite(count)) return 0
    const before = seen.get(key)
    seen.set(key, count)
    return before === undefined ? 0 : Math.max(0, count - before)
  }
}

/** The sentence for `count` new reports on `name`. */
export function describeArrivals(count, name) {
  return `${count} new report${count === 1 ? '' : 's'} on ${name}.`
}
