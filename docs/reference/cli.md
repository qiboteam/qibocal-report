# Reference: Command Line Interface (CLI)

`qibocal-report` provides report commands under `qibocal report` and local
configuration management under `qibocal config`.

```bash
qibocal report [OPTIONS] COMMAND [ARGS]...
```

---

## 💻 Commands

### `qibocal config path`

Prints the absolute server configuration directory,
`$XDG_CONFIG_HOME/qibocal/` (fallback: `~/.config/qibocal/`),
as a single plain-text line with no labels or formatting.
`QIBOCAL_REPORT_CONFIG_DIR` overrides this location. The command does not create
the directory.

Existing configurations under `qibocal-report/` are not moved automatically.
Move their files into `qibocal/` to retain registered servers, authentication data,
and notebook connections, or set `QIBOCAL_REPORT_CONFIG_DIR` to the old directory.

```bash
qibocal config path
qibocal config path | xargs -I{} ls '{}'
```

### `qibocal config clean`

Erases the local `servers.json` and `auth.json` configuration files, including
registered servers, users, invitations, password-reset links, and the signing key.
If `QIBOCAL_AUTH_FILE` points to a separate authentication file, that file is also
removed. Report data, unrelated files, configuration directories, and browser
local storage are not removed. Symbolic links are unlinked without deleting their
targets.

By default, the command lists the files and asks for confirmation, defaulting to
**No**. Stop running servers before cleaning to prevent them from recreating
configuration files.

```bash
qibocal config clean
qibocal config clean -f
```

#### Options
- `-f, --force`: Remove configuration files without interactive confirmation.
- `--help`: Show help message and exit.

---

### `qibocal report server`

Starts the FastAPI backend server and serves the embedded web application.

```bash
qibocal report server [DIRECTORY] [OPTIONS]
```

#### Arguments
- `DIRECTORY`: Target folder containing Qibocal calibration run folders. Left out, the shared reports directory is served — `$QIBOCAL_REPORT_DATA_DIR/reports`, `$XDG_DATA_HOME/qibocal/reports` or `~/.local/share/qibocal/reports` — created when missing. A named directory has to exist. With `--ssh`, both rules apply on the remote host, and nothing is checked here.

#### Options
- `--host TEXT`: Host address to bind to. Default: `localhost`.
- `--port INTEGER`: Port to listen on. Default: `8000`.
- `--auth / --no-auth`: Enable user authentication and role management, printing the initial administrator invitation. Default: `--no-auth`.
- `--name TEXT`: Name the server is registered under. Default: generated from the directory.
- `--register / --no-register`: Add the server to `servers.json`, where the dashboard finds it. `--no-register` starts it for a look and leaves the configuration alone. Default: `--register`.
- `--help`: Show help message and exit.

#### Remote options
With `--ssh`, the server runs on another machine and its address is tunnelled back; `--host` and `--port` no longer apply, since the remote server binds to its own loopback on a free port and the local end of the tunnel is what gets registered in `servers.json`.

- `--ssh TEXT`: SSH options followed by a host or `user@host` destination, as in `qibocal notebook connect`. The destination must be the last argument; do not include a remote command.
- `-w, --workdir DIRECTORY`: Working directory on the remote host. Default: a fresh temporary directory, since the server writes nothing where it starts.
- `--venv NAME_OR_PATH`: Environment on the remote host. Default: `qibocal`. Names resolve under `$XDG_CACHE_HOME/qibocal/envs/` (fallback `~/.cache/qibocal/envs/`), the same place the notebook sessions use; a missing environment is created, and an existing one without Qibocal has it installed.
- `--install TEXT`: Packages installed in that environment when it has no `qibocal`. Default: `qibocal-report`.
- `--timeout SECONDS`: Startup timeout, environment preparation included. Default: `300`.

The remote host needs an OpenSSH server and `python3` 3.10 or later; Qibocal itself is installed by the environment step. The other remote options are refused without `--ssh`.

#### Example
```bash
qibocal report server /data/calibration_runs --host 0.0.0.0 --port 8080

# The shared reports directory, under a name of your own, kept out of servers.json:
qibocal report server --name "Scratch" --no-register

# On the machine that holds the runs, in a dedicated environment:
qibocal report server /shared/calibration --ssh myuser@login --venv mychip --auth
```

---

### `qibocal report client`

Starts the standalone client web application. Useful for monitoring multiple remote servers from your workstation.

```bash
qibocal report client [OPTIONS]
```

#### Options
- `--host TEXT`: Host address to bind to. Default: `127.0.0.1`.
- `--port INTEGER`: Port to listen on. Default: `8000`.
- `--reload`: Enable auto-reload for local development. Default: `False`.
- `--help`: Show help message and exit.

#### Aliases
- `qibocal report dashboard` (backward-compatible alias).

---

### `qibocal report dev`

Starts the developer server with live Vite Hot Module Replacement (HMR) for the frontend and Uvicorn auto-reload for the backend.

```bash
qibocal report dev [DIRECTORY] [OPTIONS]
```

#### Arguments
- `DIRECTORY`: Target calibration folder. Left out, the shared reports directory is served, as for `qibocal report server`.

#### Options
- `--host TEXT`: Host address to bind to. Default: `localhost`.
- `--port INTEGER`: Backend API port. Default: `8000`.
- `--frontend-port INTEGER`: Frontend Vite dev server port. Default: `5173`.
- `--reload / --no-reload`: Toggle backend auto-reload. Default: `--reload`.
- `--auth / --no-auth`: Enable user authentication. Default: `--no-auth`.
- `--name TEXT`, `--register / --no-register`: As for `qibocal report server`.
- `--help`: Show help message and exit.

#### Aliases
- `qibocal report develop` (backward-compatible alias).

---

### `qibocal report export`

Exports the standalone frontend application for deployment to static web hosts (such as GitHub Pages).

```bash
qibocal report export [OUTPUT_DIR] [OPTIONS]
```

#### Arguments
- `OUTPUT_DIR`: Directory where static assets (`index.html`, `404.html`, `.nojekyll`, and `assets/`) will be written. Default: `./dist`.

#### Options
- `--build / --no-build`: Build from frontend source tree if present. Default: `--build`.
- `--base-path TEXT`: Base URL path for assets. Default: `./` (relative paths, compatible with GitHub Pages project subpaths).
- `--help`: Show help message and exit.

---

### `qibocal report admin list`

Lists registered administrators (or all users) stored in the local authentication database.

```bash
qibocal report admin list [OPTIONS]
```

#### Options
- `--all`: List all registered accounts (including Editors and Viewers). Default: `False`.
- `--json`: Output user details in machine-readable JSON format. Default: `False`.
- `--help`: Show help message and exit.

#### Aliases
- `qibocal report admin-list` (backward-compatible alias).

---

### `qibocal report admin invite`

Regenerates a secure invitation link for a server administrator. Useful if an administrator deleted the server from their web client interface, lost their session, or needs to recover their account.

```bash
qibocal report admin invite [USERNAME] [OPTIONS]
```

#### Arguments
- `USERNAME`: Username of the administrator. If omitted in an interactive terminal, the command displays available administrators and prompts for interactive selection.

#### Options
- `-u, --username TEXT`: Administrator username (alternative to positional argument).
- `--server-url TEXT`: Explicit base URL of the report server (e.g. `http://localhost:8000`). Default: first registered server URL or `http://localhost:8000`.
- `--host TEXT`: Server host used to build the invite URL if `--server-url` is not provided.
- `--port INTEGER`: Server port used to build the invite URL if `--server-url` is not provided.
- `-e, --expires-in-hours INTEGER`: Validity in hours (default: `168` = 7 days, `0` for never expires).
- `--interactive / --no-interactive`: Force interactive or non-interactive administrator selection.
- `--json`: Output invite details and link in machine-readable JSON format.
- `--help`: Show help message and exit.

#### Aliases
- `qibocal report invite [USERNAME]` (direct shortcut).

#### Example
```bash
# Interactive selection:
qibocal report admin invite

# Non-interactive generation for specific admin:
qibocal report admin invite alice_admin --server-url http://192.168.1.100:8000

# JSON output for automation:
qibocal report admin invite alice_admin --json
```

---

### `qibocal notebook queue [CONNECTION]`
What a SLURM queue is doing, asked once: `squeue`, `sinfo` and `whoami` run in a single round trip — over SSH when a destination is given — and answered as a table, or as JSON with `--json`. The host and the partition come from a saved `CONNECTION`, or from the options.

- `--ssh TEXT`: SSH options followed by a host or `user@host` destination.
- `-q, --queue TEXT`: the partition to look at; without it, every partition.
- `-u, --user TEXT`: only the jobs of this user.
- `-t, --state TEXT`: only jobs in this state, repeatable (`PENDING`, `RUNNING`, …).
- `--json`: the answer as JSON — `jobs`, `nodes`, `summary`, `user`, `fetched_at`, `error`.
- `--timeout FLOAT`: seconds to wait for the controller. Default `30`.

Ask sparingly: every call costs the controller something. The launcher asks every 30 seconds while a queue is on screen, and never otherwise.

## ⚙️ Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `QIBOCAL_REPORT_DIR` | Absolute path to the calibration directory scanned for reports. | Set by CLI argument |
| `QIBOCAL_FRONTEND_URL` | Used by developer mode to proxy requests to the Vite dev server. | Unset |
| `QIBOCAL_REPORT_CONFIG_DIR` | Override the directory containing server configurations and the default authentication database. | `$XDG_CONFIG_HOME/qibocal/`, falling back to `~/.config/qibocal/` |
| `XDG_CONFIG_HOME` | Default configuration root. | `~/.config/` |
| `QIBOCAL_REPORT_DATA_DIR` | Override the data directory, whose `reports/` subfolder is served when no directory is named. | `$XDG_DATA_HOME/qibocal/`, falling back to `~/.local/share/qibocal/` |
| `XDG_DATA_HOME` | Default data root. | `~/.local/share/` |
| `QIBOCAL_AUTH_FILE` | Custom authentication database path; also removed by `qibocal config clean`. | `auth.json` in the configuration directory |
| `HOME` | Determines the fallback configuration root when `XDG_CONFIG_HOME` is unset or empty. | User home |
