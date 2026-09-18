import staticDocs from '../assets/protocol_docs.json'
import { state } from '../store.js'

export const PROTOCOL_DOCS_BASE_URL = 'https://qibo.science/qibocal/stable/protocols/'

function cleanKey(str) {
  if (!str) return ''
  return String(str).toLowerCase().trim().replace(/[- \.]+/g, '_').replace(/^_+|_+$/g, '')
}

function stripStepSuffix(str) {
  if (!str) return ''
  return String(str).replace(/(?:[-_]\d+|\s+\(\d+\)|\s+\d+)$/i, '').trim()
}

/**
 * Generate candidate lookup keys from raw routine identifier and human-readable name.
 */
export function getCandidateKeys(protoId, protoName) {
  const set = new Set()
  const add = (v) => {
    if (!v) return
    const raw = String(v).trim()
    if (!raw) return
    set.add(raw)
    const cleaned = cleanKey(raw)
    if (cleaned) set.add(cleaned)
    const stripped = stripStepSuffix(raw)
    if (stripped && stripped !== raw) {
      set.add(stripped)
      const cleanStripped = cleanKey(stripped)
      if (cleanStripped) set.add(cleanStripped)
    }
  }

  add(protoId)
  add(protoName)

  // Progressive suffix reduction for composite identifiers (e.g. rabi_amplitude_signal -> rabi_amplitude -> rabi)
  const current = Array.from(set)
  for (const c of current) {
    const parts = c.split('_')
    while (parts.length > 1) {
      parts.pop()
      const prefix = parts.join('_')
      if (prefix) set.add(prefix)
    }
  }

  return Array.from(set)
}

/**
 * Checks whether a specific protocol documentation page is matched in serverDocs or staticDocs.
 *
 * @param {string} protoId
 * @param {string} protoName
 * @param {Object|null} server
 * @returns {boolean}
 */
export function hasSpecificDoc(protoId, protoName = '', server = state.activeServer) {
  const serverDocs = server?.protocol_docs || {}
  const candidates = getCandidateKeys(protoId, protoName)
  for (const c of candidates) {
    if (serverDocs[c] || staticDocs[c]) return true
  }
  return false
}

/**
 * Returns the documentation URL for a given protocol ID and name,
 * applying the active server's custom protocol_docs index on top of
 * the static protocol_docs index (masking/overriding it).
 *
 * @param {string} protoId - Protocol routine identifier (e.g. 'qubit_spectroscopy-0')
 * @param {string} protoName - Protocol human-readable name (e.g. 'Qubit Spectroscopy-0')
 * @param {Object|null} server - Server configuration object (defaults to state.activeServer)
 * @param {boolean} fallbackToMain - Whether to fall back to the main protocols URL if not specifically matched.
 * @returns {string|null} - Resolved full URL or null if fallback is disabled and no entry exists.
 */
export function getProtocolDocUrl(
  protoId,
  protoName = '',
  server = state.activeServer,
  fallbackToMain = true
) {
  if (!protoId && !protoName) {
    return fallbackToMain ? PROTOCOL_DOCS_BASE_URL : null
  }

  const serverDocs = server?.protocol_docs || {}
  const candidates = getCandidateKeys(protoId, protoName)

  // 1. Check server-level protocol_docs first (overrides static)
  for (const c of candidates) {
    if (serverDocs[c]) {
      const p = String(serverDocs[c]).trim()
      if (p.startsWith('http://') || p.startsWith('https://')) {
        return p
      }
      return `${PROTOCOL_DOCS_BASE_URL}${p.replace(/^\/+/, '')}`
    }
  }

  // 2. Check static protocol_docs index
  for (const c of candidates) {
    if (staticDocs[c]) {
      const p = String(staticDocs[c]).trim()
      if (p.startsWith('http://') || p.startsWith('https://')) {
        return p
      }
      return `${PROTOCOL_DOCS_BASE_URL}${p.replace(/^\/+/, '')}`
    }
  }

  // 3. Fallback to main protocols documentation
  return fallbackToMain ? PROTOCOL_DOCS_BASE_URL : null
}
