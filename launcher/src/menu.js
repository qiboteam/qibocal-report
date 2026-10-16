/**
 * The system menu, built from the application side.
 *
 * Menu items carry plain callbacks, so a section jump or a quick action is the
 * very same function the interface calls, with no extra event plumbing.
 */
import { isDesktop } from './bridge.js'
import { sections } from './router.js'
import { describeZoom, zoom, zoomLevel } from './zoom.js'

const MAX_QUICK_SERVERS = 8

async function build({ goTo, openDashboard, launchServer, servers, quit }) {
  const { Menu, Submenu, MenuItem, PredefinedMenuItem } = await import('@tauri-apps/api/menu')

  const separator = () => PredefinedMenuItem.new({ item: 'Separator' })
  const items = []

  items.push(await Submenu.new({
    text: 'Qibocal',
    items: [
      await MenuItem.new({
        id: 'menu-dashboard',
        text: 'Open Dashboard',
        accelerator: 'CmdOrCtrl+D',
        action: () => openDashboard()
      }),
      await separator(),
      await PredefinedMenuItem.new({ item: 'Hide' }),
      // Quitting is explicit: the window's close leaves the launcher in the
      // background; this stops what runs, waits for it, and goes.
      await MenuItem.new({
        id: 'menu-quit',
        text: 'Quit Qibocal',
        accelerator: 'CmdOrCtrl+Q',
        action: () => quit?.()
      })
    ]
  }))

  items.push(await Submenu.new({
    text: 'Edit',
    items: [
      await PredefinedMenuItem.new({ item: 'Undo' }),
      await PredefinedMenuItem.new({ item: 'Redo' }),
      await separator(),
      await PredefinedMenuItem.new({ item: 'Cut' }),
      await PredefinedMenuItem.new({ item: 'Copy' }),
      await PredefinedMenuItem.new({ item: 'Paste' }),
      await PredefinedMenuItem.new({ item: 'SelectAll' })
    ]
  }))

  const go = []
  for (const section of sections) {
    go.push(await MenuItem.new({
      id: `menu-go-${section.name}`,
      text: section.title,
      accelerator: section.accelerator,
      action: () => goTo(section.name)
    }))
  }
  go.push(await separator())
  go.push(await MenuItem.new({
    id: 'menu-go-dashboard',
    text: 'Dashboard',
    accelerator: 'CmdOrCtrl+D',
    action: () => openDashboard()
  }))
  items.push(await Submenu.new({ text: 'Go', items: go }))

  const quick = []
  for (const server of servers.slice(0, MAX_QUICK_SERVERS)) {
    quick.push(await MenuItem.new({
      id: `menu-server-${server.id}`,
      text: server.name || server.url,
      action: () => launchServer(server)
    }))
  }
  if (!quick.length) {
    quick.push(await MenuItem.new({
      id: 'menu-server-empty',
      text: 'No registered server',
      enabled: false,
      action: () => {}
    }))
  }
  items.push(await Submenu.new({
    text: 'Servers',
    items: [
      ...quick,
      await separator(),
      await MenuItem.new({
        id: 'menu-server-register',
        text: 'Register a Server…',
        accelerator: 'CmdOrCtrl+Shift+N',
        action: () => goTo('servers')
      })
    ]
  }))

  // The zoom, as every browser has it; the level is shown on the reset item.
  items.push(await Submenu.new({
    text: 'View',
    items: [
      await MenuItem.new({
        id: 'menu-zoom-in',
        text: 'Zoom In',
        accelerator: 'CmdOrCtrl+Plus',
        action: () => zoom('in')
      }),
      await MenuItem.new({
        id: 'menu-zoom-out',
        text: 'Zoom Out',
        accelerator: 'CmdOrCtrl+-',
        action: () => zoom('out')
      }),
      await MenuItem.new({
        id: 'menu-zoom-reset',
        text: `Actual Size${zoomLevel() === 1 ? '' : ` (now ${describeZoom(zoomLevel())})`}`,
        accelerator: 'CmdOrCtrl+0',
        action: () => zoom('reset')
      })
    ]
  }))

  items.push(await Submenu.new({
    text: 'Window',
    items: [
      await MenuItem.new({
        id: 'menu-window-new',
        text: 'New Window',
        accelerator: 'CmdOrCtrl+N',
        // The page one is on, again, in a window of its own: to compare two.
        action: () => window.open(window.location.href, '_blank', 'noopener')
      }),
      await separator(),
      await PredefinedMenuItem.new({ item: 'Minimize' }),
      await PredefinedMenuItem.new({ item: 'Fullscreen' }),
      // The last window closed is hidden, the launcher left in the background.
      await PredefinedMenuItem.new({ item: 'CloseWindow' })
    ]
  }))

  return Menu.new({ items })
}

/**
 * Install (or rebuild) the system menu.
 *
 * Rebuilding is how the quick actions stay in step with the registered
 * servers; failures are ignored on purpose, a missing menu must never keep
 * the interface itself from starting.
 */
export async function installMenu(handlers) {
  if (!isDesktop) return false
  try {
    const menu = await build(handlers)
    await menu.setAsAppMenu()
    return true
  } catch {
    return false
  }
}
