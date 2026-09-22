# Reference: Command Line Interface (CLI)

`qibocal-report` provides command line entry points under the `qibocal report` command group.

```bash
qibocal report [OPTIONS] COMMAND [ARGS]...
```

---

## 💻 Commands

### `qibocal report server`

Starts the FastAPI backend server and serves the embedded web application.

```bash
qibocal report server [DIRECTORY] [OPTIONS]
```

#### Arguments
- `DIRECTORY`: Target folder containing Qibocal calibration run folders. Defaults to `.` (current working directory).

#### Options
- `--host TEXT`: Host address to bind to. Default: `localhost`.
- `--port INTEGER`: Port to listen on. Default: `8000`.
- `--help`: Show help message and exit.

#### Example
```bash
qibocal report server /data/calibration_runs --host 0.0.0.0 --port 8080
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
- `DIRECTORY`: Target calibration folder. Defaults to `.`.

#### Options
- `--host TEXT`: Host address to bind to. Default: `localhost`.
- `--port INTEGER`: Backend API port. Default: `8000`.
- `--frontend-port INTEGER`: Frontend Vite dev server port. Default: `5173`.
- `--reload / --no-reload`: Toggle backend auto-reload. Default: `--reload`.
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

## ⚙️ Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `QIBOCAL_REPORT_DIR` | Absolute path to the calibration directory scanned for reports. | Set by CLI argument |
| `QIBOCAL_FRONTEND_URL` | Used by developer mode to proxy requests to the Vite dev server. | Unset |
| `HOME` | Determines configuration folder path (`~/.config/qibocal-report/`). | User home |
