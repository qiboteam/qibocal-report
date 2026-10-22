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

/** The deployed dashboard, where links lead when this page is not on the web: the desktop application's. */
export const DEPLOYED_DASHBOARD = 'https://qibo.science/qibocal-report'

/**
 * The dashboard a link should open: this very page on the web, wherever it
 * is deployed; the deployed one from the desktop application, whose pages
 * no one else can open.
 */
export function dashboardBase(location = typeof window === 'undefined' ? null : window.location) {
  if (location && /^https?:$/.test(location.protocol)) {
    return `${location.origin}${location.pathname}`.replace(/\/(index\.html)?$/, '')
  }
  return DEPLOYED_DASHBOARD
}

/**
 * The link an invitation — or a password reset — is sent as: the dashboard,
 * told the token and the server it is for, as the command line makes it.
 */
export function inviteLink(serverUrl, token, { reset = false, base = dashboardBase() } = {}) {
  const query = new URLSearchParams({ [reset ? 'reset_token' : 'token']: token, server: normalizeUrl(serverUrl) })
  return `${base}/#/invite?${query}`
}

/**
 * The link that opens a server in the dashboard, registering it first when
 * it is not yet: what a server's own page offers.
 */
export function connectLink(serverUrl, { base = dashboardBase() } = {}) {
  return `${base}/#/connect?${new URLSearchParams({ server: normalizeUrl(serverUrl) })}`
}

/** The server a connect link names: an http(s) address, normalised, or '' for anything else. */
export function connectAddress(value) {
  const text = typeof value === 'string' ? value.trim() : ''
  if (!/^https?:\/\//i.test(text)) return ''
  try {
    const url = new URL(text)
    return url.username || url.password ? '' : normalizeUrl(`${url.origin}${url.pathname}`)
  } catch {
    return ''
  }
}

/**
 * The server, and any invitation or password-reset token, of what was
 * pasted: a link `inviteLink` makes, or a plain server URL.
 */
export function parseServerAndInvite(input) {
  if (!input) return { url: '', inviteToken: null, resetToken: null }
  const str = input.trim()
  let inviteToken = null
  let resetToken = null
  let serverUrl = str

  try {
    let urlObj = null
    if (str.startsWith('http://') || str.startsWith('https://')) {
      urlObj = new URL(str)
    } else if (str.includes('/') || str.includes(':')) {
      urlObj = new URL(`http://${str}`)
    }

    if (urlObj) {
      // #/invite?token=…&server=… or #/invite?reset_token=…&server=…
      if (urlObj.hash.startsWith('#/invite?')) {
        const hashParams = new URLSearchParams(urlObj.hash.split('?')[1])
        inviteToken = hashParams.get('token')
        resetToken = inviteToken ? null : hashParams.get('reset_token')
        // A link to a dashboard names the server it is for: that, not the dashboard's own host.
        const named = hashParams.get('server')
        if (named) return { url: normalizeUrl(named), inviteToken, resetToken }
      }
      serverUrl = `${urlObj.protocol}//${urlObj.host}`
    }
  } catch {
    // Not a URL: taken as it is.
  }

  return {
    url: normalizeUrl(serverUrl),
    inviteToken,
    resetToken
  }
}
