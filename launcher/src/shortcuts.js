/**
 * The keyboard, as GitHub reads it.
 *
 * A letter after `g` goes somewhere — `g s` to Servers — `n` starts a new
 * server, `?` shows this very list, Escape puts it away. Nothing fires
 * while something is being typed, or with a modifier held: those belong to
 * the system menu, whose accelerators are the mnemonic ones. The same keys
 * work on the launcher page and on the dashboard page; what differs is how
 * a section is reached, which the caller supplies.
 */
import { sections } from './router.js'
import { state } from './state.js'

/** How long the `g` is remembered, waiting for its letter. */
const CHORD_WINDOW = 1500

/** Every shortcut, for the Help page and the cheatsheet. */
export const SHORTCUTS = [
  ...sections
    .filter(section => section.key && section.key !== '?')
    .map(section => ({ keys: ['g', section.key], what: `Go to ${section.title}`, group: 'Go to' })),
  { keys: ['g', 'd'], what: 'Open the Dashboard', group: 'Go to' },
  { keys: ['g', 'n'], what: 'Go to Notifications', group: 'Go to' },
  { keys: ['n'], what: 'New server: Servers, with the form open', group: 'Do' },
  { keys: ['?'], what: 'Show the keyboard shortcuts', group: 'Do' },
  { keys: ['Esc'], what: 'Put the shortcuts away', group: 'Do' },
  ...sections
    .filter(section => section.accelerator)
    .map(section => ({ keys: [section.accelerator], what: `${section.title}, from the Go menu`, group: 'Menu' })),
  { keys: ['CmdOrCtrl+D'], what: 'Open the Dashboard, from the Go menu', group: 'Menu' },
  { keys: ['CmdOrCtrl+N'], what: 'Register a server, from the Servers menu', group: 'Menu' }
]

/** A menu accelerator as the keys on this keyboard, for showing. */
export function describeKeys(keys, platform = typeof navigator === 'undefined' ? '' : navigator.platform) {
  const mac = /Mac|iPhone|iPad/.test(platform)
  return keys.flatMap(key => {
    if (!key.includes('+')) return [key]
    return key.split('+').map(part => {
      if (part === 'CmdOrCtrl') return mac ? '⌘' : 'Ctrl'
      if (part === 'Shift') return mac ? '⇧' : 'Shift'
      if (part === 'Comma') return ','
      return part
    })
  })
}

/** Whether a key press is for a text control, not for us. */
function typing(event) {
  const target = event.target
  if (!target || typeof target.closest !== 'function') return false
  return Boolean(target.closest('input, textarea, select, [contenteditable]:not([contenteditable="false"])'))
}

/**
 * Listen for the shortcuts; the handlers say what each does here.
 *
 * `go(name)` reaches a section, `dashboard()` opens the dashboard,
 * `newServer()` opens the Servers form. Answers the function that stops
 * listening.
 */
export function installShortcuts({ go, dashboard, newServer }) {
  let pending = null
  let timer = null

  function forget() {
    pending = null
    clearTimeout(timer)
  }

  function onKeydown(event) {
    if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) return
    if (typing(event)) return

    if (event.key === 'Escape') {
      if (state.cheatsheet) {
        state.cheatsheet = false
        event.preventDefault()
      }
      forget()
      return
    }
    if (event.key === '?') {
      state.cheatsheet = !state.cheatsheet
      event.preventDefault()
      forget()
      return
    }
    if (event.shiftKey) return

    if (pending === 'g') {
      forget()
      const key = event.key.toLowerCase()
      const section = sections.find(entry => entry.key === key)
      if (section) go(section.name)
      else if (key === 'd') dashboard()
      else if (key === 'n') go('notifications')
      else return
      state.cheatsheet = false
      event.preventDefault()
      return
    }

    if (event.key === 'g') {
      pending = 'g'
      clearTimeout(timer)
      timer = setTimeout(forget, CHORD_WINDOW)
      return
    }
    if (event.key === 'n') {
      newServer()
      state.cheatsheet = false
      event.preventDefault()
    }
  }

  document.addEventListener('keydown', onKeydown)
  return () => {
    forget()
    document.removeEventListener('keydown', onKeydown)
  }
}
