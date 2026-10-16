/**
 * A report's targets, as the list and the header show them: a qubit, or a
 * pair of qubits — a protocol on a pair has `[2, 3]` for a target, which
 * is one thing to read and to filter by, not a qubit "2,3".
 */

/** How a target reads: `Q2`, or `Q2–Q3` for a pair. */
export function targetLabel(target) {
  if (Array.isArray(target)) return target.map(targetLabel).join('–')
  return `Q${target}`
}

/** What a target is filtered by: `2`, or `2-3` for a pair, as the server reads it. */
export function targetKey(target) {
  if (Array.isArray(target)) return target.map(targetKey).join('-')
  return String(target)
}

/** Every qubit the targets touch, pairs opened up, once. */
export function flatQubits(targets = []) {
  const seen = []
  for (const target of targets) {
    for (const qubit of Array.isArray(target) ? target : [target]) {
      if (!seen.includes(qubit)) seen.push(qubit)
    }
  }
  return seen
}
