/**
 * The dashboard's keyboard, described once.
 *
 * The keys follow GitHub's: a letter after `g` goes somewhere, `?` shows
 * the list, and on a page `j`, `k`, `h` and `l` move while a letter acts
 * on what is under the cursor. Nothing fires while typing, or with a
 * modifier held, and nothing here is destructive: a key may open, move,
 * toggle or download, never delete. The pages bind the actions; this
 * module holds the words, which the cheatsheet shows — the dashboard's own
 * in a browser, the launcher's when the dashboard is embedded in it.
 */
import { ref } from 'vue'

/** Whether a key press is for a text control, or a dialog, not for us. */
export function isTypingTarget(event) {
  const target = event.target
  if (!target || typeof target.closest !== 'function') return false
  return Boolean(target.closest('input, textarea, select, [contenteditable]:not([contenteditable="false"])'))
}

/** Whether a key press is plain: no modifier that a browser or a menu would claim. */
export function isPlainKey(event) {
  return !(event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey)
}

/** Every page's keys, in the words the cheatsheet uses. */
export const PAGE_KEYS = {
  global: {
    title: 'Everywhere in the dashboard',
    keys: {
      'g s': 'Go to the report servers',
      'g l': 'Go to the report list of the active server',
      '?': 'Show the keyboard shortcuts',
      Esc: 'Put them away'
    }
  },
  dashboard: {
    title: 'The report list',
    keys: {
      '/': 'Search',
      j: 'Next report',
      k: 'Previous report',
      Enter: 'Open the report',
      Esc: 'Leave the search, or the list'
    }
  },
  report: {
    title: 'A report',
    keys: {
      b: 'Back to the search',
      v: 'Switch between slideshow and continuous',
      'j / l': 'Next protocol — the next slide, or the next card',
      'k / h': 'Previous protocol',
      '↑ / ↓': 'In a slideshow: the overview, the last protocol',
      d: 'Documentation of the selected protocol',
      x: 'Download the data of the selected protocol',
      c: 'Toggle the comments of the selected protocol, or the session\'s',
      n: 'The new platform page',
      o: 'The old platform page',
      w: 'Watch: toggle the live mode'
    }
  }
}

/** The shortcuts of a page, in the shape every cheatsheet lists. */
export function pageShortcuts(page) {
  const entry = PAGE_KEYS[page]
  if (!entry) return null
  return {
    title: entry.title,
    entries: Object.entries(entry.keys).map(([key, what]) => ({ keys: key.split(' / ').flatMap(part => part.split(' ')), what }))
  }
}

/** The page on screen, for the dashboard's own cheatsheet. */
export const currentPage = ref(null)

/** Whether the dashboard's own cheatsheet is open; the launcher has its own. */
export const cheatsheetOpen = ref(false)
