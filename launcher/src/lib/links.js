/**
 * Links into the launcher's sections, from either page of the window.
 *
 * A notification about Servers must lead there from the launcher page —
 * where the hash router listens — and from the dashboard page, where the
 * launcher page has to be loaded first. One address serves both: the hash
 * alone on the launcher page, `index.html` with the hash on the other.
 */
import { sections } from '../router.js'

/** The path of a route location, as the hash router reads it. */
export function routePath(route) {
  if (!route) return '/'
  let path = route.path
  if (!path) {
    if (route.name === 'notifications') path = '/notifications'
    else path = sections.find(section => section.name === route.name)?.path || '/'
  }
  const query = route.query ? new URLSearchParams(route.query).toString() : ''
  return query ? `${path}?${query}` : path
}

/** Whether this document is the dashboard page, rather than the launcher's. */
export function onDashboardPage(location = typeof window === 'undefined' ? null : window.location) {
  return /dashboard\.html$/.test(location?.pathname || '')
}

/** The address of a launcher route, from the page the caller is on. */
export function launcherHref(route, location) {
  return `${onDashboardPage(location) ? 'index.html' : ''}#${routePath(route)}`
}
