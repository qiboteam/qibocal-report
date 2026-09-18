import staticDocs from '../assets/protocol_docs.json'
import { state } from '../store.js'

export const PROTOCOL_DOCS_BASE_URL = 'https://qibo.science/qibocal/stable/protocols/'

/**
 * Returns the documentation URL for a given protocol ID and name,
 * applying the active server's custom protocol_docs index on top of
 * the static protocol_docs index (masking/overriding it).
 *
 * @param {string} protoId - Protocol routine identifier (e.g. 'qubit_spectroscopy')
 * @param {string} protoName - Protocol human-readable name (e.g. 'Qubit Spectroscopy')
 * @param {Object|null} server - Server configuration object (defaults to state.activeServer)
 * @returns {string|null} - Resolved full URL or null if no documentation entry exists.
 */
export function getProtocolDocUrl(protoId, protoName = '', server = state.activeServer) {
  if (!protoId && !protoName) return null

  // 1. Check server-level protocol_docs (additional index, overrides static)
  const serverDocs = server?.protocol_docs || {}

  const cleanId = (protoId || '').toLowerCase().trim().replace(/[- ]+/g, '_')
  const cleanName = (protoName || '').toLowerCase().trim().replace(/[- ]+/g, '_')

  let relativeOrFull =
    serverDocs[protoId] ??
    serverDocs[cleanId] ??
    serverDocs[protoName] ??
    serverDocs[cleanName] ??
    staticDocs[protoId] ??
    staticDocs[cleanId] ??
    staticDocs[protoName] ??
    staticDocs[cleanName]

  if (!relativeOrFull) return null

  relativeOrFull = String(relativeOrFull).trim()
  if (relativeOrFull.startsWith('http://') || relativeOrFull.startsWith('https://')) {
    return relativeOrFull
  }

  const cleanPath = relativeOrFull.replace(/^\/+/, '')
  return `${PROTOCOL_DOCS_BASE_URL}${cleanPath}`
}
