# Qibocal Launcher

The desktop application: it spawns `qibocal` processes, manages the
configuration shared with the command line, and embeds the web dashboard so
there is no context switch between starting an instance and browsing its
reports.

The user-facing documentation lives in
[`docs/user-guide/launcher.md`](../docs/user-guide/launcher.md).

## Layout

```
launcher/
├── index.html          launcher page
├── dashboard.html      the web frontend, embedded
├── src/
│   ├── bridge.js       the only module talking to the native side
│   ├── state.js        reactive store, native events, toasts
│   ├── menu.js         the system menu, built from the sections
│   ├── router.js       the sections, shared by router, home page and menu
│   ├── lib/            pure logic, covered by `pnpm run test`
│   ├── components/
│   └── views/
└── src-tauri/
    ├── src/
    │   ├── settings.rs config files shared with the CLI
    │   ├── qibocal.rs  interpreter discovery and short-lived CLI calls
    │   └── process.rs  the supervisor of long-running processes
    └── icon.svg        source of the icon set
```

The dashboard is **not** forked: `dashboard.html` mounts `../frontend/src`
through the `@dashboard` alias, with the same stylesheet and the same UnoCSS
theme. The frontend keeps being built and deployed on its own; the launcher
only bundles it as a second page of the same window, which is what lets both
halves share `localStorage` and, with it, the registered servers.

## Development

```bash
pnpm install
pnpm run icons   # writes src-tauri/icons/, required before any build
pnpm run app     # Tauri development window
pnpm run test    # node:test, no build needed
```

`pnpm run dev` serves the pages in a plain browser, which is enough to work on
the styling: every native call then fails with a clear message instead of
crashing.

`pnpm run app:build` produces the installers for the current platform;
[`.github/workflows/launcher.yml`](../.github/workflows/launcher.yml) produces
them for all three, on demand and on every release.

## Notes

- There is no `pnpm-lock.yaml`: the dependencies are the frontend's, pinned
  there, plus the Tauri packages that have to follow the toolchain the build
  machine provides. CI installs with `--no-frozen-lockfile`.
- `src-tauri/icons/` is generated from `icon.svg` and not committed, so the
  repository holds no binaries.
- Processes are stopped with a signal, not a kill, and only killed if they are
  still around a few seconds later: `qibocal notebook connect` needs that window
  to close its SSH tunnels and remote workers.
