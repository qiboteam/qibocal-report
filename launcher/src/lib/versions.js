/**
 * Which qibocal-report goes into the launcher's own environment.
 *
 * The choice is a pip requirement, stored as `package` in `launcher.json`:
 * a release from PyPI, or a branch or tag of the repository installed from
 * its archive — no git needed on the machine. Until the first release, the
 * default is the main branch. The lists come from PyPI and the GitHub API,
 * fetched by the interface; everything here is pure and tested.
 */

export const PROJECT = 'qibocal-report'
export const REPOSITORY = 'qiboteam/qibocal-report'
export const PYPI_URL = `https://pypi.org/pypi/${PROJECT}/json`
export const BRANCHES_URL = `https://api.github.com/repos/${REPOSITORY}/branches?per_page=100`
export const TAGS_URL = `https://api.github.com/repos/${REPOSITORY}/tags?per_page=100`

const ARCHIVE = `https://github.com/${REPOSITORY}/archive/refs`

/** A branch or tag, as pip installs it: the archive of that ref. */
export function archiveSpec(kind, ref) {
  const folder = kind === 'tag' ? 'tags' : 'heads'
  return `${PROJECT} @ ${ARCHIVE}/${folder}/${encodeURIComponent(ref)}.tar.gz`
}

export function releaseSpec(version) {
  return `${PROJECT}==${version}`
}

/** What the launcher installs when nothing was chosen. Kept in step with qibocal.rs. */
export const DEFAULT_SPEC = archiveSpec('branch', 'main')

/**
 * The choice behind a requirement: `{ kind, ref }` with kind `release`,
 * `branch`, `tag` or `other` — the last for anything typed by hand.
 */
export function parseSpec(spec) {
  const text = typeof spec === 'string' ? spec.trim() : ''
  if (!text) return parseSpec(DEFAULT_SPEC)
  const release = text.match(new RegExp(`^${PROJECT}\\s*==\\s*([^\\s;]+)$`))
  if (release) return { kind: 'release', ref: release[1] }
  const archive = text.match(new RegExp(`^${PROJECT}\\s*@\\s*${ARCHIVE}/(heads|tags)/(.+)\\.tar\\.gz$`))
  if (archive) {
    return { kind: archive[1] === 'tags' ? 'tag' : 'branch', ref: decodeURIComponent(archive[2]) }
  }
  return { kind: 'other', ref: text }
}

/** A short label for a requirement, for the lists and the status line. */
export function describeSpec(spec) {
  const { kind, ref } = parseSpec(spec)
  if (kind === 'release') return `${ref} (PyPI)`
  if (kind === 'branch') return `branch ${ref}`
  if (kind === 'tag') return `tag ${ref}`
  return ref
}

function compareVersions(left, right) {
  const parts = value => value.split(/[.\-+]/).map(part => (/^\d+$/.test(part) ? Number(part) : part))
  const a = parts(left)
  const b = parts(right)
  for (let i = 0; i < Math.max(a.length, b.length); i += 1) {
    if (a[i] === undefined) return -1
    if (b[i] === undefined) return 1
    if (a[i] === b[i]) continue
    if (typeof a[i] === 'number' && typeof b[i] === 'number') return a[i] - b[i]
    return String(a[i]) < String(b[i]) ? -1 : 1
  }
  return 0
}

/** The releases of the PyPI JSON document, newest first, yanked ones left out. */
export function parseReleases(document) {
  const releases = document && typeof document === 'object' ? document.releases : null
  if (!releases || typeof releases !== 'object') return []
  return Object.entries(releases)
    .filter(([, files]) => Array.isArray(files) && files.length && files.some(file => !file?.yanked))
    .map(([version]) => version)
    .sort((left, right) => compareVersions(right, left))
}

/** The names of the GitHub branches or tags, `main` first, the rest as given. */
export function parseRefs(list) {
  const names = (Array.isArray(list) ? list : [])
    .map(entry => (typeof entry?.name === 'string' ? entry.name : ''))
    .filter(Boolean)
  return [...names.filter(name => name === 'main'), ...names.filter(name => name !== 'main')]
}

/**
 * The options offered by the picker: every release, branch and tag, with the
 * current choice kept even when the lists do not know it.
 */
export function versionOptions({ releases = [], branches = [], tags = [], current = '' } = {}) {
  const options = [
    ...releases.map(version => ({ spec: releaseSpec(version), kind: 'release', label: describeSpec(releaseSpec(version)) })),
    ...branches.map(name => ({ spec: archiveSpec('branch', name), kind: 'branch', label: describeSpec(archiveSpec('branch', name)) })),
    ...tags.map(name => ({ spec: archiveSpec('tag', name), kind: 'tag', label: describeSpec(archiveSpec('tag', name)) }))
  ]
  const chosen = typeof current === 'string' ? current.trim() : ''
  if (chosen && !options.some(option => option.spec === chosen)) {
    options.push({ spec: chosen, kind: parseSpec(chosen).kind, label: describeSpec(chosen) })
  }
  return options
}
