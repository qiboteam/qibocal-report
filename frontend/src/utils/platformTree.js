/**
 * Utility functions for parsing and manipulating platform JSON trees
 * (parameters.json and calibration.json).
 *
 * Rules:
 * - A scalar value (number, string, boolean, null) is a leaf.
 * - A list where all elements are numbers (e.g. [value, error] or coordinates) is ALSO a leaf.
 * - Non-leaf objects and arrays of non-numbers form hierarchical branches.
 */

/**
 * Check if a value is an array consisting solely of numbers (or empty).
 */
export function isNumberList(val) {
  if (!Array.isArray(val)) return false
  if (val.length === 0) return true
  return val.every(item => typeof item === 'number' || item === null)
}

/**
 * Check if a value is a leaf node according to the platform specification.
 */
export function isLeaf(val) {
  if (val === null || val === undefined) return true
  if (typeof val !== 'object') return true
  if (isNumberList(val)) return true
  return false
}

/**
 * Human-friendly string formatting for numbers.
 */
export function formatNumber(num) {
  if (num === null || num === undefined) return 'null'
  if (typeof num !== 'number') return String(num)
  if (Number.isInteger(num)) return num.toLocaleString()

  const abs = Math.abs(num)
  if (abs >= 1e9) {
    return (num / 1e9).toFixed(4).replace(/\.?0+$/, '') + ' GHz'
  }
  if (abs >= 1e6) {
    return (num / 1e6).toFixed(4).replace(/\.?0+$/, '') + ' MHz'
  }
  if (abs >= 1e3 && abs < 1e5) {
    return (num / 1e3).toFixed(3).replace(/\.?0+$/, '') + ' kHz'
  }
  if (abs > 0 && abs < 0.0001) {
    return num.toExponential(3)
  }
  return Number(num.toFixed(6)).toString()
}

/**
 * Format a leaf value for presentation in the UI.
 */
export function formatLeafDisplay(val) {
  if (val === null) return { text: 'null', raw: 'null', type: 'null' }
  if (val === undefined) return { text: 'undefined', raw: 'undefined', type: 'null' }
  if (typeof val === 'boolean') return { text: val ? 'true' : 'false', raw: String(val), type: 'boolean' }
  if (typeof val === 'number') return { text: formatNumber(val), raw: String(val), type: 'number' }
  if (typeof val === 'string') return { text: val, raw: val, type: 'string' }

  if (Array.isArray(val)) {
    if (val.length === 0) return { text: '[]', raw: '[]', type: 'empty-list' }

    // Qibocal 2-element tuple typically represents [value, error]
    if (val.length === 2 && typeof val[0] === 'number') {
      const v = formatNumber(val[0])
      const e = val[1] !== null ? formatNumber(val[1]) : 'null'
      return {
        text: `${v} ± ${e}`,
        raw: JSON.stringify(val),
        type: 'uncertainty-pair',
        val: val[0],
        err: val[1]
      }
    }

    // Generic list of numbers
    const items = val.map(v => (v === null ? 'null' : formatNumber(v)))
    return {
      text: `[ ${items.join(', ')} ]`,
      raw: JSON.stringify(val),
      type: 'number-list'
    }
  }

  return { text: String(val), raw: String(val), type: 'unknown' }
}

/**
 * Check if a value is a pulse sequence (e.g. in native_gates):
 * An array of [channelName, eventObject] where eventObject has a 'kind'.
 */
export function isPulseSequence(val) {
  if (!Array.isArray(val) || val.length === 0) return false
  return val.every(item => {
    return (
      Array.isArray(item) &&
      item.length === 2 &&
      typeof item[0] === 'string' &&
      item[1] &&
      typeof item[1] === 'object' &&
      typeof item[1].kind === 'string'
    )
  })
}

/**
 * Recursively build a structured tree from an arbitrary JSON object.
 */
export function buildTreeNode(key, value, path = '', depth = 0) {
  const currentPath = path ? `${path}.${key}` : String(key)

  if (isLeaf(value)) {
    return {
      id: currentPath || 'root',
      key: String(key),
      path: currentPath,
      isLeaf: true,
      value,
      depth
    }
  }

  // Native gates pulse sequence detection
  if (isPulseSequence(value)) {
    return {
      id: currentPath || 'root',
      key: String(key),
      path: currentPath,
      isLeaf: false,
      isPulseSequence: true,
      pulseSequence: value,
      leafEntries: [],
      branchEntries: [],
      totalLeavesCount: value.length,
      totalBranchesCount: 0,
      depth
    }
  }

  const leafEntries = []
  const branchEntries = []

  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      const childNode = buildTreeNode(`[${index}]`, item, currentPath, depth + 1)
      if (childNode.isLeaf) {
        leafEntries.push(childNode)
      } else {
        branchEntries.push(childNode)
      }
    })
  } else if (value && typeof value === 'object') {
    Object.entries(value).forEach(([k, v]) => {
      const childNode = buildTreeNode(k, v, currentPath, depth + 1)
      if (childNode.isLeaf) {
        leafEntries.push(childNode)
      } else {
        branchEntries.push(childNode)
      }
    })
  }

  let totalLeaves = leafEntries.length
  let totalBranches = branchEntries.length

  branchEntries.forEach(b => {
    totalLeaves += b.totalLeavesCount || 0
    totalBranches += b.totalBranchesCount || 0
  })

  return {
    id: currentPath || 'root',
    key: String(key),
    path: currentPath,
    isLeaf: false,
    leafEntries,
    branchEntries,
    totalLeavesCount: totalLeaves,
    totalBranchesCount: totalBranches,
    depth
  }
}

/**
 * Filter tree nodes based on a search term matching key names or leaf values.
 */
export function filterTree(node, query) {
  if (!query || !query.trim()) {
    return { node, matches: true, hasMatchingDescendant: true }
  }

  const q = query.toLowerCase().trim()
  const keyMatches = node.key.toLowerCase().includes(q) || node.path.toLowerCase().includes(q)

  if (node.isLeaf) {
    const display = formatLeafDisplay(node.value)
    const valMatches = String(display.raw || display.text).toLowerCase().includes(q)
    const matches = keyMatches || valMatches
    return { node, matches, hasMatchingDescendant: matches }
  }

  if (node.isPulseSequence) {
    const rawSeq = JSON.stringify(node.pulseSequence || '').toLowerCase()
    const seqMatches = keyMatches || rawSeq.includes(q)
    return { node, matches: seqMatches, hasMatchingDescendant: seqMatches }
  }

  const filteredLeaves = node.leafEntries.filter(l => {
    const lKeyMatches = l.key.toLowerCase().includes(q) || l.path.toLowerCase().includes(q)
    const display = formatLeafDisplay(l.value)
    const lValMatches = String(display.raw || display.text).toLowerCase().includes(q)
    return lKeyMatches || lValMatches
  })

  const filteredBranches = []
  let anyChildMatches = filteredLeaves.length > 0

  for (const b of node.branchEntries) {
    const result = filterTree(b, query)
    if (result.hasMatchingDescendant || result.matches) {
      filteredBranches.push(result.node)
      anyChildMatches = true
    }
  }

  const matches = keyMatches || anyChildMatches

  const filteredNode = {
    ...node,
    leafEntries: keyMatches ? node.leafEntries : filteredLeaves,
    branchEntries: keyMatches ? node.branchEntries : filteredBranches,
    totalLeavesCount: (keyMatches ? node.leafEntries : filteredLeaves).length,
    totalBranchesCount: (keyMatches ? node.branchEntries : filteredBranches).length
  }

  return {
    node: filteredNode,
    matches,
    hasMatchingDescendant: anyChildMatches
  }
}
