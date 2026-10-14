# Qibocal, the desktop application

Named after the command line it drives, there being nothing else to confuse it
with: it spawns `qibocal` processes, edits the configuration shared with them,
and embeds the web dashboard so there is no context switch between starting an
instance and browsing its reports.

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
│   ├── dashboard.js    the embedded page: the menu again, and the overlay
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

There is no navigation bar: the header holds the logo on the left and the
dashboard button on the right, and the sections are reached through the **Go**
menu `menu.js` builds from `router.js`. `dashboard.js` installs that same menu
on the embedded page — where the window has navigated away from `index.html`,
so the launcher's own callbacks are gone — and mounts `LauncherOverlay.vue`,
the way back, on the one dashboard route with room for it.

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
- The published builds are unsigned, so macOS and Windows block them on first
  launch; the way around it is in
  [the user guide](../docs/user-guide/launcher.md#opening-an-unsigned-build).
  The workflow signs and notarizes the macOS bundle as soon as the secrets
  `APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD`, `APPLE_SIGNING_IDENTITY`,
  `APPLE_ID`, `APPLE_PASSWORD` and `APPLE_TEAM_ID` exist, and warns in the job
  summary while they do not.
