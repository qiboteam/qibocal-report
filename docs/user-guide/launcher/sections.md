# Desktop Launcher: Sections & Windows

The home page opens onto every section — **Running** first, then what there is to start — and each of them is one jump away — from its card, from the **Go** system menu with its keyboard shortcuts, or from the keyboard alone.

- **Dashboard** (`Cmd/Ctrl+D`, or `g d`): the complete report browser, with the servers the launcher knows already connected.
- **Servers** (`Cmd/Ctrl+Shift+S`, or `g s`): one form for a new server, wherever it runs — here, on another machine, or already reachable — and the registered ones with their invitations.
- **Running** (`Cmd/Ctrl+Shift+R`, or `g r`): the live output of everything the launcher started, with graceful stop.
- **Notebooks** (`Cmd/Ctrl+Shift+B`, or `g b`): open JupyterLab or Marimo sessions, locally, over SSH or through SLURM.
- **Remote execution** (`Cmd/Ctrl+Shift+E`, or `g e`): where qibocal-widgets runs a notebook's acquisitions, and the reports of those runs.
- **Agents** (`Cmd/Ctrl+Shift+A`, or `g a`): the configurations of the Qibocal MCP servers, here and on access nodes, and autonomous agent runs.
- **Configuration** (`Cmd/Ctrl+,`, or `g c`): install or update Qibocal, and edit the files shared with the command line.
- **Help** (`Cmd/Ctrl+/`): this guide, inside the application, and every keyboard shortcut.

Under the cards, **Running now** names what is alive at the moment, in a line each: the server, session or installation, with the way to its card in **Running** and the way to where it is used — the dashboard for a server, the browser for a notebook, **Configuration** for an installation of `qibocal-report`.

## Windows

A second window shows another page next to the first — two reports, a report and the servers, the launcher and the dashboard. **Window → New Window** (`Cmd/Ctrl+N`, as in every browser) opens the page one is on again, in a window of its own. Wherever something opens — the Dashboard card, a server's **Open**, a report in the dashboard's list — a modifier held while clicking (command or control, or shift), the middle button, or `Shift+Enter` on the keyboard opens it in a new window instead. The context menu's *Open Link in New Window* works too, on every link; a report's row or card in the dashboard's list, which is not a link, has a menu of its own on right-click — *Open*, *Open in New Window*. Links that leave the application open in the browser, as before. Each window is a page of the same application, so they share the servers, the notifications and the processes; closing one of several closes it alone, and closing the last is closing the application. There are no tabs.

## In the background

Closing a window does not stop anything. The last window on screen is hidden rather than closed — `Cmd/Ctrl+W`, the close button, it is the same — and the launcher stays in the background, its servers and notebook sessions with it, as Teams or Telegram do. It comes back from its icon in the system tray — the menu bar on macOS — the Q alone, drawn as the system draws its own: on macOS a template image, painted black or white to suit the menu bar, elsewhere white, or black on a light Windows taskbar. Its menu offers **Open Qibocal** and **Quit Qibocal**; a click on the icon opens it directly on Linux and Windows; on macOS the dock icon does the same. Quitting is explicit: **Quit Qibocal** in the application menu, `Cmd/Ctrl+Q`, or the tray's item stops what runs, waits for it — the closing dialog lists whom it waits for, and offers to go without waiting — and exits; nothing is ever left behind.

While the launcher is in the background, or behind another window, or on another of its pages, what happens is also said by the system: a notification when a server comes up or a notebook session is ready, when one of them fails, and when new reports appear on a registered server — the dashboard asks each server for its count every minute, inside the launcher only. Everything is in the bell and the Notifications page as well.

## Zoom

The interface zooms as a browser does: `Cmd/Ctrl` with `+` and `-` steps the level up and down through the usual stops, from 50% to 300%, `Cmd/Ctrl+0` returns to the actual size, and the wheel with `Cmd/Ctrl` held — or a pinch on a trackpad — does the same; the **View** menu has the three, with the current level named on *Actual Size*. The level is remembered, and is the same on the launcher's pages, on the dashboard's, and in every window.
