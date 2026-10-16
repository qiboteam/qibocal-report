# Desktop Launcher: Report Servers

## 🚀 A new server

**Servers** opens on the servers it has; the **New server** button at the top unfolds one form, whatever the server turns out to be. It opens on a **Name** — drawn as the command line draws them, an adjective and a scientist such as *zen-bohr*, and free to overwrite — and on where the server runs:

- **This machine** runs `qibocal` here.
- **Another machine** reaches a host over SSH, prepares an environment there, and tunnels the server back.
- **Already running** registers an address, starting nothing: any Qibocal report server you can reach.

The fields below follow that choice, so what does not apply is not there, and they keep one convention throughout the launcher: a field that is **required** says so next to its label and is drawn white and outlined; the grey ones are optional, with their default stated underneath, and the circled *i* holds the longer explanation. What is rarely changed sits under **More options**, folded. The command about to be run is spelled out under the form, so the equivalent command line is never a mystery.

**Start and register** is the default: the server is started and written to `servers.json` straight away — the same file `qibocal` reads, so a server started from the command line shows up in the launcher, and the other way around. **Start** starts it for a look instead: it shows up in **Running** and in the dashboard as long as it runs, and in a *Running, not registered* list on this page, with a **Register** button in case it turns out to be worth keeping — the same **Register** its card in **Running** offers, and the `r` key there.

### On this machine

| Mode | Command | Use |
| --- | --- | --- |
| Reports | `qibocal report server` | Serve a directory of calibration runs |
| Developer | `qibocal report dev` | Live interface with hot reloading |

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

Stopping is graceful and never holds the window: a server or a session is told to stop, its card reads *stopping…* meanwhile, and whatever is still there after six seconds is killed. Closing the window, or quitting, while something runs is the same stop for everything at once, behind a dialog listing what is being waited for, each with a wheel until it is gone: the application closes by itself when the last one has stopped, or at once with **Force close** — which is also how a second close, or a second quit, is read.

Every registered server offers one main action, by its state. While it runs, **Open** jumps to the bundled dashboard with that instance selected — servers are read in the dashboard, not in a browser. While it does not, **Start** brings it up: with the options it was last started with, or, for one the launcher never started, on this machine at its registered address, serving the shared directory; a server registered at another machine's address has nothing to start here, and the button says so. Besides it, **Invite** re-issues an administrator invitation — choose the administrator, or leave the field empty for the initial, unregistered one, and the validity in hours; the link can then be copied and sent — **Update** brings the server's `qibocal-report` up to date and starts it again, keeping its entry: a server on another machine has the package put back by force in its own environment there — which otherwise keeps what it holds for good, since the environment is only filled when it has no qibocal — with `qibocal report server upgrade`, run as a process of its own that shows in **Running**, the server starting again once it is done; a server on this machine runs the launcher's own installation, which is updated first, as **Configuration** does. A running server is stopped for it. **Edit** opens the very form of the registration on everything known about the server: its name, address and description, as `servers.json` holds them, and how it is started — the machine it runs on, the SSH destination, the environment, the directory, the ports, every option — which is what **Start** uses next time; *Already running* means the launcher is not to start it at all. A server that is running wears a *running* pill, which leads to its card in **Running**. A server started again over SSH comes back at a new tunnel address, and its entry moves there rather than gaining a twin.

**Running** has one card per server or session, with every run of it since the application was opened: the latest on top, the earlier ones below, each folded until wanted. A running server opens in the dashboard — registering it, if it was started for a look — and a running notebook in the browser, at its local address; one that has stopped offers **Start again**, with the options it was started with, and the new run joins its card. Stopping is graceful: the process is asked to terminate and gets a few seconds to close SSH tunnels and remote workers before it is killed, which matters for notebook sessions. Closing the application stops everything it started.
