# Desktop Launcher: Configuration

**Configuration** lists the files in the shared configuration directory — `$QIBOCAL_REPORT_CONFIG_DIR`, `$XDG_CONFIG_HOME/qibocal` or `~/.config/qibocal`:

| File | Contents |
| --- | --- |
| `servers.json` | Registered report servers |
| `notebooks.json` | Saved notebook connections |
| `auth.json` | Users, invitations and signing keys |
| `launcher.json` | Launcher preferences |

A click on a file opens it on its contents: the registered servers, the saved connections, the users, the preferences — one row per entry, named as the rest of the application names it. A click on a row unfolds it into fields, marked by the accent line down its left, where the entry is edited or removed; the last row adds one. **Edit as JSON** swaps the fields for the text of the file, checked as it is typed, with **Save** out of reach while the JSON is broken — which is also how a file the editor cannot structure is repaired. Saving replaces the file in one step and reloads the sections that read it, so a server renamed here is renamed in **Servers** at once; **Revert** goes back to what is on disk.

`auth.json` is editable too, behind a warning: it holds the users, the invitations and the signing keys, and changing the keys signs everyone out exactly as deleting the file does.

The directory can be revealed in the system file manager, and the files ticked deleted with **Delete selected** next to it — the graphical counterpart of `qibocal config clean`. Deleting `auth.json` signs every user out and clears the administrators, exactly as it does from the command line; the circled *i* on the button says so.

## Formats and versions

Every file declares the format it was written in: an object with a `version`, holding its entries under `servers` (`servers.json`), under `connections` (`notebooks.json`), or next to the version (`auth.json`, `launcher.json`). A file without a version was written before versions were, and is read as the current format. A file of another version — written by a newer or older Qibocal — is read by nothing, launcher or command line, and never written over: it is listed apart, under **Unknown configuration**, with the format it declares, and opens as the JSON it is. There is no automatic migration, on purpose: the formats still change too often for one to be worth its history. Migrating by hand means editing that JSON until it declares the current format, at which point the file is read again.

---

## 🔗 Relationship with the web client

The dashboard inside the application and the one at <https://qibo.science/qibocal-report> are the same application, built from the same sources. The launcher only adds what a browser cannot do, and a way back: on **Report Servers** — the only page with room for it — the logo appears in the top-left corner, in the same position it occupies everywhere else, and returns to the launcher, and the status bar runs along the bottom edge as it does everywhere else. The **Go** menu and its shortcuts work from the dashboard as well. Whatever the dashboard has to say inside the application — a server connected, a token copied, plots regenerated — is said where everything else is, in the status bar and the **Notifications** page, never as a toast of its own; on the dashboard's inner pages, which fill their edges with their own interface, a bell at the right end of the toolbar opens the same bubble as the status bar's. In a browser, the dashboard keeps its toasts. The two halves share one list of servers, `servers.json`: a server registered in the launcher is in the dashboard at once, and one added, renamed or removed in the dashboard's own **Report Servers** page is written to the same file, where the launcher and the command line find it. Inside the application that page has two parts: **Managed by the launcher**, the servers the launcher has started, shown only while they run — opening one from **Running** or **Servers** registers it, if it was started for a look — and **Registered independently**, everything else.
