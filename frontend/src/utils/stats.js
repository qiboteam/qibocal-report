import { state, resolveAuthor } from '../store.js'

export function computeStatsFromReports(reports, server = state.activeServer) {
  if (!reports || reports.length === 0) {
    return {
      authors: [],
      tags: [],
      labels: [],
      protocols: [],
      date_histogram: [],
      platforms: [],
      author_frequencies: [],
      tag_frequencies: [],
      total_reports: 0
    }
  }

  const authorsSet = new Set()
  const labelsSet = new Set()
  const protoMap = new Map()
  const platformMap = new Map()
  const authorMap = new Map()
  const tagMap = new Map()
  const dateMap = new Map()

  for (const r of reports) {
    if (r.author) {
      const canonical = resolveAuthor(r.author, server)
      authorsSet.add(canonical)
      authorMap.set(canonical, (authorMap.get(canonical) || 0) + 1)
    }
    if (r.platform) {
      platformMap.set(r.platform, (platformMap.get(r.platform) || 0) + 1)
    }
    for (const p of (r.protocols || [])) {
      protoMap.set(p, (protoMap.get(p) || 0) + 1)
    }
    for (const t of (r.tags || r.labels || [])) {
      labelsSet.add(t)
      tagMap.set(t, (tagMap.get(t) || 0) + 1)
    }
    if (r.date) {
      dateMap.set(r.date, (dateMap.get(r.date) || 0) + 1)
    }
  }

  const protocols = Array.from(protoMap.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)

  const platforms = Array.from(platformMap.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)

  const author_frequencies = Array.from(authorMap.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)

  const tag_frequencies = Array.from(tagMap.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)

  const date_histogram = Array.from(dateMap.entries())
    .map(([date, count]) => ({ date, count }))
    .sort((a, b) => a.date.localeCompare(b.date))

  return {
    authors: Array.from(authorsSet).sort(),
    tags: Array.from(labelsSet).sort(),
    labels: Array.from(labelsSet).sort(),
    protocols,
    platforms,
    author_frequencies,
    tag_frequencies,
    date_histogram,
    total_reports: reports.length
  }
}
