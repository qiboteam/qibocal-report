# User Guide: Desktop Launcher

The **Qibocal Launcher** is the desktop application that does what a web page is not allowed to do: reach the machine it runs on. It starts report servers and notebook sessions, manages the configuration shared with the command line, re-issues administrator invitations — and embeds the very same dashboard that is deployed on the web, so there is no context switch between launching an instance and browsing its reports.

---

## 📦 Installation

Installers for the three desktop platforms are attached to every [release](https://github.com/qiboteam/qibocal-report/releases):

| Platform | File | Notes |
| --- | --- | --- |
| macOS | `.dmg` | Universal binary, Intel and Apple silicon |
| Linux | `.deb`, `.AppImage` | The AppImage needs no installation |
| Windows | `-setup.exe`, `.msi` | The installer sets the application up for the current user |

The builds are unsigned: macOS asks for a confirmation in **System Settings → Privacy & Security** the first time, Windows SmartScreen offers *More info → Run anyway*.

The launcher drives the `qibocal` command line, it does not replace it: install Qibocal as usual (see [Getting Started](user-guide/quickstart)) and the launcher will find it.

---

## 🏠 Sections

The home page opens onto every section, and each of them is one jump away — through the top navigation, or through the **Go** system menu with its keyboard shortcuts.

- **Dashboard** (`Cmd/Ctrl+D`): the complete report browser, with the servers the launcher knows already connected.
- **Servers**: start a server on this machine, register a reachable one, re-issue administrator invitations.
- **Running**: the live output of everything the launcher started, with graceful stop.
- **Notebooks**: open JupyterLab or Marimo sessions, locally, over SSH or through SLURM.
- **Configuration**: pick the Qibocal installation and inspect the files shared with the command line.

The **Servers** system menu lists the registered instances: picking one starts it again with the options it was last started with.

---

## ⚙️ Finding Qibocal

The launcher looks for the `qibocal` command line, in order, in:

1. the installation explicitly chosen in **Configuration**;
2. the `QIBOCAL_EXECUTABLE` environment variable;
3. the `PATH`;
4. the usual places — `~/.local/bin`, pipx environments, `.venv` folders, `/usr/local/bin`, `/opt/homebrew/bin`.

A graphical application does not inherit the shell environment on macOS, so the first run often needs the installation to be pointed out once, in **Configuration → Choose environment…**. A virtual environment folder is enough: the launcher looks inside its `bin` (or `Scripts`) directory. The choice is remembered in `launcher.json`, next to the other configuration files.

---

## 🚀 Starting a server

**Servers → Start a server here** covers the three serving modes, each mapping onto a command:

| Mode | Command | Use |
| --- | --- | --- |
| Reports | `qibocal report server` | Serve a directory of calibration runs |
| Client | `qibocal report client` | Browse other servers, serving none |
| Developer | `qibocal report dev` | Live interface with hot reloading |

Pick the reports directory with the file browser, and the address with the host and port fields — **Free port** asks the operating system for one nobody is listening on. The **User accounts** switch is the `--auth` flag: it enables authentication and produces the initial administrator invitation, which appears in the output of the running server.

The command about to be run is spelled out under the form, so the equivalent command line is never a mystery.

Starting a server registers it in `servers.json`, which is the same file `qibocal` reads — a server started from the command line shows up in the launcher, and the other way around.

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

**Notebooks** is the graphical face of `qibocal notebook`. Every option of the command line is a control:

- **SSH destination** — empty for a local session.
- **SLURM partition** and **extra srun options**.
- **Working directory**, chosen with the file browser for local sessions.
- **Kernel environment** on the computing node.
- **Computing node subnet**, validated the way Python's `ip_network` validates it: a network with host bits set is refused before the command is run.
- **Interface**: JupyterLab or Marimo.
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

Files can be revealed in the system file manager, and selected ones deleted — the graphical counterpart of `qibocal config clean`. Deleting `auth.json` signs every user out and clears the administrators, exactly as it does from the command line.

---

## 🔗 Relationship with the web client

The dashboard inside the application and the one at <https://qibo.science/qibocal-report> are the same application, built from the same sources. The launcher only adds what a browser cannot do, and a bar to step back into it. Servers registered by the launcher are published to the embedded dashboard, so an instance started in one section is immediately browsable in the other.
