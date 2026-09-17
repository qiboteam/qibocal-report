/**
 * URL normalization and resolution utilities.
 */

/**
 * Normalizes a URL string by trimming whitespace, stripping trailing slashes,
 * and ensuring an http:// or https:// protocol prefix.
 */
export function normalizeUrl(url) {
  if (!url) return ''
  let clean = url.trim().replace(/\/+$/, '')
  if (!clean.startsWith('http://') && !clean.startsWith('https://')) {
    clean = `http://${clean}`
  }
  return clean
}

/**
 * Returns the base API URL for an active server object, or empty string for local.
 */
export function getActiveServerUrl(activeServer) {
  if (activeServer?.url) {
    return normalizeUrl(activeServer.url)
  }
  return ''
}

/**
 * Resolves a relative API path against the active server base URL.
 */
export function getApiUrl(path, activeServer) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  const base = getActiveServerUrl(activeServer)
  if (base) {
    return `${base}${cleanPath}`
  }
  return cleanPath
}

/**
 * Resolves a WebSocket URL for the given path against the active server.
 */
export function getActiveWsUrl(path, activeServer) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  const serverUrl = getActiveServerUrl(activeServer)
  if (serverUrl) {
    const wsBase = serverUrl.replace(/^http:\/\//i, 'ws://').replace(/^https:\/\//i, 'wss://')
    return `${wsBase}${cleanPath}`
  }
  const isHttps = typeof window !== 'undefined' && window.location?.protocol === 'https:'
  const wsProto = isHttps ? 'wss:' : 'ws:'
  const host = (typeof window !== 'undefined' && window.location?.host) || '127.0.0.1:8000'
  return `${wsProto}//${host}${cleanPath}`
}
