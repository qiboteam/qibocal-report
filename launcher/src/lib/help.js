/**
 * The pages of the Help section: the Desktop Launcher section of the
 * documentation, as the dashboard lists it, its overview first. Pure, and
 * covered by `tests/help.test.js`.
 */
import { DEFAULT_DOCS_NAV, resolveDocLink } from '../../../frontend/src/utils/docsNav.js'

export const GUIDE_PATH = 'user-guide/launcher'

export function helpPages(nav = DEFAULT_DOCS_NAV) {
  const section = nav.find(entry => entry.path === GUIDE_PATH)
  const items = (section?.items || []).map(item => ({ name: item.path.slice(GUIDE_PATH.length + 1), title: item.title }))
  return [{ name: 'index', title: 'Overview' }, ...items]
}

/**
 * Where a link on Help page `current` leads, resolved as the dashboard's
 * Documentation resolves it: `{ kind: 'anchor', id }` within the page,
 * `{ kind: 'page', name, id }` to another Help page, `{ kind: 'docs', page,
 * id }` to a page of the documentation outside this guide — which the
 * application holds too, in its dashboard — or `{ kind: 'url', url }`
 * anywhere else, the only kind left to the browser.
 */
export function helpTarget(href, current = 'index') {
  const here = current === 'index' ? GUIDE_PATH : `${GUIDE_PATH}/${current}`
  const link = resolveDocLink(href, here)
  if (link.kind !== 'doc') return link
  if (link.page === GUIDE_PATH) return { kind: 'page', name: 'index', id: link.id }
  if (link.page.startsWith(`${GUIDE_PATH}/`)) return { kind: 'page', name: link.page.slice(GUIDE_PATH.length + 1), id: link.id }
  return { kind: 'docs', page: link.page, id: link.id }
}
