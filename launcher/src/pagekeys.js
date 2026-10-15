/**
 * The keys that mean something on one page only, described once.
 *
 * Every list page reads the same way: `j` and `k` walk the list — the one
 * under the cursor wears an outline — and a letter acts on it, as GitHub
 * does with its own lists. The pages bind the actions; the Help page and
 * the cheatsheet take the words from here, so the three never disagree.
 */
export const PAGE_KEYS = {
  home: {
    title: 'Home',
    keys: {
      j: 'Next card',
      k: 'Previous card',
      Enter: 'Open the card'
    }
  },
  servers: {
    title: 'Servers',
    keys: {
      j: 'Next registered server',
      k: 'Previous registered server',
      Enter: 'Open it in the dashboard while it runs; start it otherwise',
      s: 'Start it, or open it when it is running',
      e: 'Edit it',
      i: 'Invite an administrator'
    }
  },
  processes: {
    title: 'Running',
    keys: {
      j: 'Next card',
      k: 'Previous card',
      o: 'Open it: the dashboard for a server, the browser for a notebook',
      x: 'Stop it',
      s: 'Start it again',
      l: 'Unfold or fold its latest run'
    }
  },
  notebooks: {
    title: 'Notebooks',
    keys: {
      j: 'Next connection',
      k: 'Previous connection',
      Enter: 'Open a session with the form as it is',
      o: 'Open a session with the form as it is'
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
  dashboard: {
    title: 'Dashboard: the report list',
    keys: {
      '/': 'Search',
      j: 'Next report',
      k: 'Previous report',
      Enter: 'Open the report',
      Esc: 'Leave the search, or the list'
    }
  },
  report: {
    title: 'Dashboard: a report',
    keys: {
      '←': 'Previous slide',
      '→': 'Next slide',
      '↑': 'The overview',
      '↓': 'The last protocol'
    }
  }
}

/** The shortcuts of a page, in the shape the cheatsheet and Help list. */
export function pageShortcuts(page) {
  const entry = PAGE_KEYS[page]
  if (!entry) return null
  return {
    title: entry.title,
    entries: Object.entries(entry.keys).map(([key, what]) => ({ keys: [key], what }))
  }
}
