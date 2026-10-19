/**
 * The keys that mean something on one page only, described once.
 *
 * Every list page reads the same way: `j` and `k` walk the list — the one
 * under the cursor wears an outline — and a letter acts on it, as GitHub
 * does with its own lists. The pages bind the actions; the Help page and
 * the cheatsheet take the words from here, so the three never disagree.
 */
import { PAGE_KEYS as DASHBOARD_KEYS } from '@dashboard/utils/shortcuts.js'

export const PAGE_KEYS = {
  home: {
    title: 'Home',
    keys: {
      'h / j / k / l': 'Move over the cards as a grid; below them, the lines of what runs',
      Enter: 'Open the card, or the card in Running of what runs',
      'Shift Enter': 'The same, in a new window',
      o: 'Where what runs is used: the dashboard, the browser, Configuration'
    }
  },
  servers: {
    title: 'Servers',
    keys: {
      j: 'Next registered server',
      k: 'Previous registered server',
      Enter: 'Open it in the dashboard while it runs; start it otherwise',
      'Shift Enter': 'Open it in the dashboard, in a new window',
      s: 'Start it, or open it when it is running',
      e: 'Edit it',
      i: 'Invite an administrator',
      d: 'Duplicate it: the form for a new server, with its options',
      u: 'Update its qibocal-report, and start it again'
    }
  },
  processes: {
    title: 'Running',
    keys: {
      j: 'Next card — the selection itself',
      k: 'Previous card',
      Enter: 'Open it: the dashboard for a server, the browser for a notebook',
      'Shift Enter': 'A server in the dashboard, in a new window',
      o: 'Open it: the dashboard for a server, the browser for a notebook',
      x: 'Stop it',
      s: 'Start it again',
      r: 'Register it, when it was started for a look',
      l: 'Unfold its latest run',
      h: 'Fold it again',
      q: 'The SLURM queue of the selected session, on its page'
    }
  },
  settings: {
    title: 'Configuration',
    keys: {
      j: 'Next configuration file',
      k: 'Previous configuration file',
      Enter: 'Open the file, or close it'
    }
  },
  notebooks: {
    title: 'Notebooks',
    keys: {
      j: 'Next registered session',
      k: 'Previous registered session',
      Enter: 'Open it in the browser while it runs; start it otherwise',
      s: 'Start it, or open it when it is running',
      e: 'Edit it',
      d: 'Duplicate it: the form for a new session, with its options'
    }
  },
  notifications: {
    title: 'Notifications',
    keys: {
      j: 'Next notification',
      k: 'Previous notification',
      Enter: 'Go where it points',
      e: 'Mark it done, or bring it back',
      x: 'Delete it'
    }
  },
  // The dashboard's pages describe their own keys, in the frontend package,
  // so the web has them too; here they are listed under the dashboard's name.
  ...Object.fromEntries(
    Object.entries(DASHBOARD_KEYS).map(([page, entry]) => [
      `dashboard-${page}`,
      { ...entry, title: `Dashboard · ${entry.title}` }
    ])
  )
}

/** The shortcuts of a page, in the shape the cheatsheet and Help list. */
export function pageShortcuts(page) {
  if (page && typeof page === 'object') return page
  const entry = PAGE_KEYS[page]
  if (!entry) return null
  return {
    title: entry.title,
    entries: Object.entries(entry.keys).map(([key, what]) => ({
      keys: key.split(' / ').flatMap(part => part.split(' ')),
      what
    }))
  }
}
