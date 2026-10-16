/**
 * The zoom level of the interface: the steps a browser offers, kept across
 * pages and windows. Pure, and covered by `tests/zoom.test.js`; applying
 * it to the webview is `zoom.js`'s business.
 */

/** The levels, as browsers step through them; 1 is the default. */
export const ZOOM_LEVELS = [0.5, 0.67, 0.75, 0.8, 0.9, 1, 1.1, 1.25, 1.5, 1.75, 2, 2.5, 3]

export const ZOOM_KEY = 'qibocal_launcher_zoom'

/** A stored level, or 1 for nothing or nonsense. */
export function parseZoom(value) {
  const level = Number(value)
  if (!Number.isFinite(level) || level < ZOOM_LEVELS[0] || level > ZOOM_LEVELS[ZOOM_LEVELS.length - 1]) return 1
  return level
}

/** The level one step up or down from `level`; the end stays put. */
export function stepZoom(level, direction) {
  const current = parseZoom(level)
  if (direction > 0) return ZOOM_LEVELS.find(entry => entry > current + 1e-9) ?? current
  return [...ZOOM_LEVELS].reverse().find(entry => entry < current - 1e-9) ?? current
}

/** The level as it is shown: a percentage. */
export function describeZoom(level) {
  return `${Math.round(parseZoom(level) * 100)}%`
}

/**
 * What a key press asks of the zoom, or null: `+` or `=` with the command
 * or control key steps up, `-` down, `0` resets. The numeric keypad's keys
 * count too.
 */
export function zoomRequest(event) {
  if (!event || !(event.metaKey || event.ctrlKey) || event.altKey) return null
  const key = event.key
  if (key === '+' || key === '=' || key === 'Add') return 'in'
  if (key === '-' || key === '_' || key === 'Subtract') return 'out'
  if (key === '0' || key === 'Insert' && event.code === 'Numpad0') return 'reset'
  return null
}
