/**
 * Server names, generated the way the command line generates them.
 *
 * `qibocamp report server` registers an instance as an adjective and a
 * scientist — "zen-bohr", "swift-curie" — and a server added from here or
 * from the launcher should not read differently. The two lists are copied
 * from `qibocamp.config`, and a test on that side holds them equal.
 */
export const ADJECTIVES = [
  'zen',
  'clever',
  'brave',
  'quantum',
  'eager',
  'swift',
  'calm',
  'keen',
  'bold',
  'radiant',
  'lucid',
  'serene',
  'agile',
  'stellar'
]

export const SCIENTISTS = [
  'bohr',
  'curie',
  'feynman',
  'dirac',
  'planck',
  'fermi',
  'bell',
  'schrodinger',
  'einstein',
  'wu',
  'aspect',
  'zeilinger',
  'clauser'
]

function pick(list, random) {
  return list[Math.floor(random() * list.length) % list.length]
}

/**
 * A fresh name, avoiding the ones in use.
 *
 * The combinations are few enough that a long-lived list could exhaust
 * them: after a bounded number of draws, a numbered suffix settles it.
 */
export function generateServerName(taken = [], random = Math.random) {
  const used = new Set(
    (Array.isArray(taken) ? taken : [])
      .map(name => (typeof name === 'string' ? name.trim() : ''))
      .filter(Boolean)
  )
  let candidate = ''
  for (let attempt = 0; attempt < 32; attempt += 1) {
    candidate = `${pick(ADJECTIVES, random)}-${pick(SCIENTISTS, random)}`
    if (!used.has(candidate)) return candidate
  }
  let suffix = 2
  while (used.has(`${candidate}-${suffix}`)) suffix += 1
  return `${candidate}-${suffix}`
}
