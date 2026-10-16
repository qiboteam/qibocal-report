/**
 * The pages of the Help section: the Desktop Launcher section of the
 * documentation, as the dashboard lists it, its overview first. Pure, and
 * covered by `tests/help.test.js`.
 */
import { DEFAULT_DOCS_NAV } from '../../../frontend/src/utils/docsNav.js'

export const GUIDE_PATH = 'user-guide/launcher'
/** The deployed dashboard, whose Documentation holds every other page. */
export const DOCS_URL = 'https://qibo.science/qibocal-report/#/docs/'

export function helpPages(nav = DEFAULT_DOCS_NAV) {
  const section = nav.find(entry => entry.path === GUIDE_PATH)
  const items = (section?.items || []).map(item => ({ name: item.path.slice(GUIDE_PATH.length + 1), title: item.title }))
  return [{ name: 'index', title: 'Overview' }, ...items]
}

/**
 * Where a link in a page leads: `{ kind: 'anchor', id }` within the page,
 * `{ kind: 'page', name, id }` to another Help page, `{ kind: 'url', url }`
 * anywhere else — a page of the documentation outside this guide opens in
 * the deployed dashboard. Links between pages are written as the dashboard
 * reads them, from the root of the documentation.
 */
export function helpTarget(href) {
  const text = String(href || '').trim()
  if (!text) return { kind: 'url', url: null }
  if (text.startsWith('#')) return { kind: 'anchor', id: text.slice(1) }
  if (/^(https?:|mailto:)/i.test(text)) return { kind: 'url', url: text }
  const [path, id = null] = text.replace(/^\/+/, '').replace(/^docs\//, '').split('#')
  const clean = path.replace(/\.md$/, '').replace(/\/$/, '')
  if (clean === GUIDE_PATH) return { kind: 'page', name: 'index', id }
  if (clean.startsWith(`${GUIDE_PATH}/`)) return { kind: 'page', name: clean.slice(GUIDE_PATH.length + 1), id }
  return { kind: 'url', url: `${DOCS_URL}${clean}${id ? `#${id}` : ''}` }
}
