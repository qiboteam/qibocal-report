/**
 * Where a report can be uploaded, and what the answer of a destination
 * means. Pure, and covered by `tests/uploads.test.js`.
 */
import { normalizeUrl } from './url.js'

/** The registered servers a report on `source` can go to: every other one. */
export function uploadDestinations(servers = [], source = null) {
  const from = normalizeUrl(source?.url || '')
  return (Array.isArray(servers) ? servers : []).filter(server => {
    const url = normalizeUrl(server?.url || '')
    return url && url !== from
  })
}

/**
 * What a destination's capability answer means for the picker:
 * `ready` to upload, `sign-in` when the server would take it from a
 * signed-in user — a registered one, or one to register first — and
 * `refused` when this account may not upload there.
 */
export function uploadState(capability, { registered = true, signedIn = false } = {}) {
  if (!capability) return { state: 'unreachable', text: 'Not reachable.' }
  if (capability.accepted) return { state: 'ready', text: capability.auth_enabled ? 'You may upload here.' : 'Accepts uploads.' }
  if (!capability.auth_enabled) return { state: 'refused', text: 'Does not accept uploads.' }
  if (!registered) return { state: 'sign-in', text: 'Requires signing in: register it to authenticate.' }
  if (!signedIn) return { state: 'sign-in', text: 'Sign in to this server to upload.' }
  return { state: 'refused', text: 'Your account may not upload here.' }
}

/** A failed upload's answer, as a short reason. */
export function uploadFailure(status, detail = '') {
  if (status === 409) return detail || 'Already on that server.'
  if (status === 413) return detail || 'Larger than that server accepts.'
  if (status === 401) return 'Sign in to that server first.'
  if (status === 403) return 'Your account may not upload there.'
  return detail || `The server answered ${status}.`
}
