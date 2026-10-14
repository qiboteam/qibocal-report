# User Guide: Desktop Launcher

**Qibocal** is the desktop application that does what a web page is not allowed to do: reach the machine it runs on. It carries the name of the command line it drives — there is no other Qibocal application — and is called *the launcher* in this page wherever the two have to be told apart. It starts report servers and notebook sessions, here or on another machine over SSH, edits the configuration shared with the command line, re-issues administrator invitations — and embeds the very same dashboard that is deployed on the web, so there is no context switch between launching an instance and browsing its reports.

---

## 📦 Installation

Installers for the three desktop platforms are attached to every [release](https://github.com/qiboteam/qibocal-report/releases):

| Platform | File | Notes |
| --- | --- | --- |
| macOS | `.dmg` | Universal binary, Intel and Apple silicon |
| Linux | `.deb`, `.AppImage` | The AppImage needs no installation |
| Windows | `-setup.exe`, `.msi` | The installer sets the application up for the current user |

The launcher drives the `qibocal` command line, it does not replace it — and it installs it itself, in an environment of its own, the first time it starts (see [Installing Qibocal](#installing-qibocal)). A Python 3.10 or newer on the machine is all it needs.

### Opening an unsigned build

Signing an application for macOS requires a paid Apple Developer ID, and one for Windows a certificate from a commercial authority. Until the project holds them, the published installers are unsigned, and both systems refuse them on first launch — the application is intact, the operating system simply has nobody to check it with.

On **macOS**, the first attempt is met with *"Qibocal" Not Opened — Apple could not verify "Qibocal" is free of malware*. Only **Done** and **Move to Bin** are offered, and the application is *not* the one to insist with:

1. press **Done**;
2. open **System Settings → Privacy & Security** and scroll to the security section, where *"Qibocal" was blocked to protect your Mac* now appears;
3. press **Open Anyway**, and confirm.

The same can be done in one command, which drops the quarantine flag the browser attached to the download:

```bash
xattr -dr com.apple.quarantine /Applications/Qibocal.app
```

Either way the answer is remembered: subsequent launches open directly.

On **Windows**, SmartScreen shows *Windows protected your PC*: choose **More info → Run anyway**. On **Linux** nothing is in the way — the `.deb` and the AppImage install and run as they are.

Maintainers who do hold the credentials only have to set the repository secrets `APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD` and `APPLE_SIGNING_IDENTITY` — plus `APPLE_ID`, `APPLE_PASSWORD` and `APPLE_TEAM_ID` for notarization: the build workflow picks them up on its own, and the installers it publishes then open with a double click.

---

## 🏠 Sections

The home page opens onto every section, and each of them is one jump away — from its card, or from the **Go** system menu with its keyboard shortcuts.

- **Dashboard** (`Cmd/Ctrl+D`): the complete report browser, with the servers the launcher knows already connected.
- **Servers** (`Cmd/Ctrl+2`): one form for a new server, wherever it runs — here, on another machine, or already reachable — and the registered ones with their invitations.
- **Running** (`Cmd/Ctrl+3`): the live output of everything the launcher started, with graceful stop.
- **Notebooks** (`Cmd/Ctrl+4`): open JupyterLab or Marimo sessions, locally, over SSH or through SLURM.
- **Configuration** (`Cmd/Ctrl+5`): install or update Qibocal, and edit the files shared with the command line.

The header carries no navigation of its own: the logo in the top-left corner returns to the home page, the button in the top-right opens the dashboard, and everything else is in the **Go** menu, which works from the dashboard too. The **Servers** system menu lists the registered instances: picking one starts it again with the options it was last started with.

---

## ⚙️ Installing Qibocal

Nothing to do: when the launcher starts and finds no Qibocal, it installs one in the background, in an environment of its own, and says so with a spinner in the header while it works — the output is in **Running**, as for everything else it starts. The environment lives in `~/.cache/qibocal/envs/launcher` (or `$XDG_CACHE_HOME/qibocal/envs/launcher`), next to the ones the notebook sessions make. All this needs is a Python 3.10 or newer on the machine: the launcher looks on the `PATH` and in the usual places — Homebrew, `/usr/local`, the python.org installers, pyenv — and says so, in **Configuration**, when it finds none. Should the installation fail, the same page offers **Install Qibocal** to try again, and **Update** reinstalls the chosen version with its dependencies brought up to date.

Until `qibocal-report` has a release on PyPI, what gets installed is the **`main` branch**, from the repository archive — no `git` is needed. A server installed that way serves its API without the bundled web page, which is no loss here: the launcher's own dashboard is the client.

The launcher then uses, in order:

1. the environment chosen in the developer options;
2. its own installation;
3. the `QIBOCAL_EXECUTABLE` environment variable;
4. the `PATH`;
5. the usual places — `~/.local/bin`, pipx environments, `.venv` folders, `/usr/local/bin`, `/opt/homebrew/bin`.

The **developer options**, folded under the installation, hold two things. **Version** picks what goes into the launcher's environment — the releases on PyPI, the branches and the tags of the repository, fetched when the page opens, or *something else*: any requirement `pip install` accepts, a local checkout included. **Save version** stores the choice in `launcher.json`, and the button above becomes **Switch to …** while the installed version differs from the chosen one. **Another environment** is for a checkout of `qibocal-report`: **Choose environment…** and **Choose executable…** point the launcher at an environment that already has Qibocal — a virtual environment folder is enough, the launcher looks inside its `bin` (or `Scripts`) directory — and **Detect again** goes back to its own installation. Both choices live in `launcher.json`, next to the other configuration files.

---

## 🚀 A new server

**Servers → New server** is one form, whatever the server turns out to be. It opens on a **Name** — drawn as the command line draws them, an adjective and a scientist such as *zen-bohr*, and free to overwrite — and on where the server runs:

- **This machine** runs `qibocal` here.
- **Another machine** reaches a host over SSH, prepares an environment there, and tunnels the server back.
- **Already running** registers an address, starting nothing: any Qibocal report server you can reach.

The fields below follow that choice, so what does not apply is not there, and they keep one convention throughout the launcher: a field that is **required** says so next to its label and is drawn white and outlined; the grey ones are optional, with their default stated underneath, and the circled *i* holds the longer explanation. What is rarely changed sits under **More options**, folded. The command about to be run is spelled out under the form, so the equivalent command line is never a mystery.

**Start** is the default and starts the server for a look: it shows up in **Running** and in the dashboard as long as it runs, and in a *Running, not registered* list on this page, with a **Register** button in case it turns out to be worth keeping. **Start and register** writes it to `servers.json` straight away — the same file `qibocal` reads, so a server started from the command line shows up in the launcher, and the other way around.

### On this machine

| Mode | Command | Use |
| --- | --- | --- |
| Reports | `qibocal report server` | Serve a directory of calibration runs |
| Developer | `qibocal report dev` | Live interface with hot reloading |
| Client | `qibocal report client` | Browse other servers, serving none |

The **Reports directory** is optional: left empty, the shared one is served — `~/.local/share/qibocal/reports`, or `$XDG_DATA_HOME/qibocal/reports`, created when it is not there yet — which is where runs go when they have no better home. Under **More options**, the host and port fields pick the address, and **Free port** asks the operating system for one nobody is listening on; the **User accounts** switch is the `--auth` flag: it enables authentication and produces the initial administrator invitation, which appears in the output of the running server. The server starts from a fresh temporary directory, since it writes nothing where it starts.

### On another machine

The form becomes `qibocal report server --ssh …`: the server runs where the calibration runs are, and only its address is brought back.

- **SSH destination** — options and a `user@host` destination, the way `qibocal notebook connect` takes them. Host aliases, agent authentication and jump hosts from the SSH configuration all work; the destination must come last.
- **Reports directory** — a path on *that* machine, typed rather than browsed, since the file dialog only sees this one. Optional here too: empty, the shared reports directory *of that machine* is served, created when missing.
- **Server environment** — a name resolved under `~/.cache/qibocal/envs/`, or an absolute path. If it does not exist it is created and the package is installed into it; if it exists without Qibocal, the package is added. Nothing else in it is touched. This is the same rule, and the same cache, the notebook sessions use.
- **Working directory** — where to move before starting, for relative paths; a fresh temporary directory by default.
- **Package to install** — `qibocal-report` by default; a pinned version or a different distribution is accepted.

The last three sit under **More options**: their defaults are the right ones for a first try.

There are no host and port fields: the remote server binds to its own loopback on a free port, and the launcher opens an SSH tunnel to it, so the address that ends up in **Running** and in `servers.json` is a local one. Nothing is exposed on the remote network. Stopping the process closes the tunnel and the remote server with it.

The remote machine needs an OpenSSH server and `python3` 3.10 or later — not Qibocal, which is what the environment step installs.

---

## 📡 Handling running servers

Every registered server offers:

- **Open**: jump to the bundled dashboard with that instance selected.
- **Start**: run it again with the options used last time, without filling the form.
- **Invite**: re-issue an administrator invitation. Choose the administrator — or leave the field empty for the initial, unregistered one — and the validity in hours; the link can then be copied and sent.
- **Browser**: open the instance in the system browser instead of the application.

**Running** shows the live output of each process. Stopping is graceful: the process is asked to terminate and gets a few seconds to close SSH tunnels and remote workers before it is killed, which matters for notebook sessions. Closing the application stops everything it started.

---

## 📓 Notebook sessions

**Notebooks** is the graphical face of `qibocal notebook`. Every option of the command line is a control, and none is required — empty, the session is a local one:

- **SSH destination** — empty for a local session.
- **SLURM partition**, and **Interface**: JupyterLab or Marimo.

Under **More options**, with their defaults:

- **Extra srun options**.
- **Working directory**, chosen with the file browser for local sessions.
- **Kernel environment** on the computing node, `qibocal` by default, under the same `~/.cache/qibocal/envs/` as the launcher's own environment.
- **Computing node subnet**, validated the way Python's `ip_network` validates it: a network with host bits set is refused before the command is run.
- **Startup timeout**.

Named connections are read from and written to `notebooks.json`, the file `qibocal notebook add` manages, so a connection saved here is usable as `qibocal notebook connect <name>`. Only the options that differ from the defaults are stored.

Opening a session runs it with `--no-interactive`: the address appears in **Running** as soon as the session answers.

---

## 🗂️ Configuration

**Configuration** lists the files in the shared configuration directory — `$QIBOCAL_REPORT_CONFIG_DIR`, `$XDG_CONFIG_HOME/qibocal` or `~/.config/qibocal`:

| File | Contents |
| --- | --- |
| `servers.json` | Registered report servers |
| `notebooks.json` | Saved notebook connections |
| `auth.json` | Users, invitations and signing keys |
| `launcher.json` | Launcher preferences |

A click on a file opens it on its contents: the registered servers, the saved connections, the users, the preferences — one row per entry, named as the rest of the application names it. A click on a row unfolds it into fields, marked by the accent line down its left, where the entry is edited or removed; the last row adds one. **Edit as JSON** swaps the fields for the text of the file, checked as it is typed, with **Save** out of reach while the JSON is broken — which is also how a file the editor cannot structure is repaired. Saving replaces the file in one step and reloads the sections that read it, so a server renamed here is renamed in **Servers** at once; **Revert** goes back to what is on disk.

`auth.json` is editable too, behind a warning: it holds the users, the invitations and the signing keys, and changing the keys signs everyone out exactly as deleting the file does.

Files can also be revealed in the system file manager, and the ones ticked deleted — the graphical counterpart of `qibocal config clean`. Deleting `auth.json` signs every user out and clears the administrators, exactly as it does from the command line.

---

## 🔗 Relationship with the web client

The dashboard inside the application and the one at <https://qibo.science/qibocal-report> are the same application, built from the same sources. The launcher only adds what a browser cannot do, and a way back: on **Report Servers** — the only page with room for it — the logo appears in the top-left corner, in the same position it occupies everywhere else, and returns to the launcher. The **Go** menu and its shortcuts work from the dashboard as well. Servers registered by the launcher are published to the embedded dashboard, so an instance started in one section is immediately browsable in the other.
