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
 * Resolves a WebSocket URL for the given path against the active server,
 * optionally including an authentication token.
 */
export function getActiveWsUrl(path, activeServer, token = null) {
  let cleanPath = path.startsWith('/') ? path : `/${path}`
  if (token) {
    const separator = cleanPath.includes('?') ? '&' : '?'
    cleanPath = `${cleanPath}${separator}token=${encodeURIComponent(token)}`
  }
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

/**
 * Parses user input to extract server base URL and any invite token.
 * Supports:
 * - http://127.0.0.1:8000/#/invite?token=xyz
 * - http://127.0.0.1:8000/?invite=xyz
 * - http://127.0.0.1:8000/invite/xyz
 * - Plain server URLs
 */
export function parseServerAndInvite(input) {
  if (!input) return { url: '', inviteToken: null }
  const str = input.trim()
  let inviteToken = null
  let serverUrl = str

  try {
    let urlObj = null
    if (str.startsWith('http://') || str.startsWith('https://')) {
      urlObj = new URL(str)
    } else if (str.includes('/') || str.includes(':')) {
      urlObj = new URL(`http://${str}`)
    }

    if (urlObj) {
      // 1. Search in query params
      if (urlObj.searchParams.get('token')) {
        inviteToken = urlObj.searchParams.get('token')
      } else if (urlObj.searchParams.get('invite')) {
        inviteToken = urlObj.searchParams.get('invite')
      }

      // 2. Search in hash query params (#/invite?token=...)
      if (!inviteToken && urlObj.hash && urlObj.hash.includes('?')) {
        const hashQuery = urlObj.hash.split('?')[1]
        const hashParams = new URLSearchParams(hashQuery)
        inviteToken = hashParams.get('token') || hashParams.get('invite')
      }

      // 3. Search in path (/invite/<token>)
      if (!inviteToken && urlObj.pathname) {
        const parts = urlObj.pathname.split('/').filter(Boolean)
        const invIdx = parts.findIndex(p => p.toLowerCase() === 'invite')
        if (invIdx >= 0 && parts[invIdx + 1]) {
          inviteToken = parts[invIdx + 1]
        }
      }

      serverUrl = `${urlObj.protocol}//${urlObj.host}`
    }
  } catch {
    // If not a standard URL, fallback
  }

  return {
    url: normalizeUrl(serverUrl),
    inviteToken
  }
}

