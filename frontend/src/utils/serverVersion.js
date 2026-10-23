/**
 * What a server says it is, `GET /api/version`, against what this dashboard
 * reads: the API version counts the breaking changes, so one other than
 * ours is a server to update — or a dashboard, when the server's is newer.
 */

/** The API version this dashboard speaks. */
export const API_VERSION = 1

/**
 * How a server's version answer reads here: `{ state, label, title }`, the
 * state `ok`, `older`, `newer` or `unknown` — no answer, a server from
 * before the first release.
 */
export function serverCompatibility(info) {
  if (!info || typeof info.api_version !== 'number') {
    return { state: 'unknown', label: 'version unknown', title: 'This server does not say its version: it predates the first release, update it.' }
  }
  const label = `v${info.version}`
  const built = info.commit ? ` (commit ${String(info.commit).slice(0, 7)})` : ''
  if (info.api_version === API_VERSION) {
    return { state: 'ok', label, title: `Qibocamp Server ${info.version}${built}, API v${info.api_version}` }
  }
  const older = info.api_version < API_VERSION
  return {
    state: older ? 'older' : 'newer',
    label: `${label} · API v${info.api_version}`,
    title: older
      ? `This server speaks API v${info.api_version}, older than this dashboard's v${API_VERSION}: update the server.`
      : `This server speaks API v${info.api_version}, newer than this dashboard's v${API_VERSION}: reload or update the dashboard.`
  }
}
