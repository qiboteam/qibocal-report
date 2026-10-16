<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/qibocal_logo_light.svg" />
  <img src="docs/assets/qibocal_logo_dark.svg" alt="Qibocal" width="300" style="margin: 1.2rem 0;" />
</picture>

**Modern, lightweight web application and high-throughput server to explore, analyze, and manage [Qibocal](https://github.com/qiboteam/qibocal) calibration reports interactively.**

[![Python](https://img.shields.io/badge/python-3.10+-purple.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/frontend-Vue_3-42b883.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Website](https://img.shields.io/badge/website-qibo.science-833dff.svg)](https://qibo.science)

</div>

`qibocal-report` provides a user interface around the
[Qibocal](https://github.com/qiboteam/qibocal) calibration library.
It helps users manage the calibration workflow, from interactive notebook
sessions to exploring results and organizing runs across report servers.

## ⚡ Key Features

- **Interactive Visualizations**: Explore calibration reports with interactive 2D and 3D plots, inspect protocol results, and download data and platform configurations.
- **Live Reports**: Follow running calibrations with automatic updates that regenerate only new or changed protocol plots.
- **Multi-Server Dashboard**: Connect to and manage local or remote report servers from one place.
- **Search & Filters**: Find calibration runs by title, platform, author, protocol, tag, or date.
- **Statistics Dashboard**: Follow calibration activity over time and explore trends across protocols, authors, and platforms.
- **Batch Actions**: Organize multiple runs at once by updating tags and authors, or deleting reports.
- **Desktop Launcher**: Start servers and notebook sessions, here or on another machine over SSH, edit the local configuration, and browse reports from a single cross-platform application.

## 🚀 Quick Start

### 1. Installation

Install using `pip`:

```bash
pip install qibocal-report
```

### 2. Serving Reports (CLI)

Point `qibocal report server` to any directory containing Qibocal calibration runs:

```bash
qibocal report server ./sample_data --port 8000
```

The server is headless: it answers its API at `http://localhost:8000`, and no
page. It is read by the dashboard — deployed at
[qibo.science/qibocal-report](https://qibo.science/qibocal-report), where the
server's address is added under **Servers** — or by the desktop application
below. Without a directory, the shared one under
`~/.local/share/qibocal/reports` is served, and created if it is not there yet.

The runs often live on another machine. Add `--ssh` and the server starts there
instead, in a managed environment, and is tunnelled back to a local address:

```bash
qibocal report server /shared/calibration --ssh myuser@login --venv mychip
```

The remote host only needs an OpenSSH server and Python 3.10+; the environment
is created and `qibocal-report` installed into it on first use, exactly as for
notebook sessions.

### Interactive Notebooks

Start JupyterLab locally, over SSH, or on a SLURM partition:

```bash
qibocal notebook connect
qibocal notebook connect --ssh myuser@login -q mychip -w /shared/calibration
qibocal notebook connect --marimo --venv ./calibration-env -n
```

The command opens an authenticated local URL and stays attached until Ctrl+C.
Use `--marimo` for Marimo instead of JupyterLab, or `-n` to print the URL without
opening a browser. Save reusable connections with `qibocal notebook add`.

Use `--venv NAME_OR_PATH` to select the default kernel environment. JupyterLab
also lists all managed kernel environments and environments previously selected
for Jupyter with `--venv` on the computing node, with distinct labels.

See **`man qibocal`** ([source](data/share/man/man1/qibocal.1)) for connection
management, environment setup, networking requirements, and configuration
examples, or `qibocal notebook connect --help` for command options.

### 3. Developer Mode (Live HMR)

For developers modifying the frontend or backend:

```bash
qibocal report dev ./sample_data
```

Starts the FastAPI backend with auto-reload and the Vite frontend dev server at `http://localhost:5173` with instant Hot Module Replacement.

### 4. The Dashboard

The dashboard is a static single-page application, built from
[`frontend/`](frontend/) and deployed to GitHub Pages at
[qibo.science/qibocal-report](https://qibo.science/qibocal-report) by
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) on every push to
`main`. The report servers do not serve it — they stay headless — and the Python
package does not carry it: it connects to any number of servers from the
browser, and the desktop launcher embeds the very same pages. To build it by
hand:

```bash
cd frontend && pnpm run build
```

Navigation uses hash URLs so that refreshing or sharing a page works on static
hosts without server-side routing. The deployment path is preserved: for example,
the hosted documentation is at
[`https://qibo.science/qibocal-report/#/docs`](https://qibo.science/qibocal-report/#/docs).
Static exports also work at other subpaths without configuring the router.

### 5. Desktop Launcher

The [launcher](launcher/) is a desktop application that does what the web page cannot: it
reaches the machine it runs on. It starts report servers and notebook sessions,
manages the configuration shared with the CLI, re-issues administrator
invitations, and embeds the very same dashboard, so launching an instance and
browsing its reports happen in one application.

Installers for macOS, Linux and Windows are attached to every
[release](https://github.com/qiboteam/qibocal-report/releases), and
[`.github/workflows/launcher.yml`](.github/workflows/launcher.yml) also builds
them on demand. To run it from the sources:

```bash
cd launcher
pnpm install
pnpm run icons   # generates the application icons from icon.svg
pnpm run app     # or `pnpm run app:build` for the installers
```

## 📖 Documentation

The documentation covers report and server management, calibration results and
exports, development and architecture, and CLI and API references.
Select **Documentation** in the application's navigation, or open **`/#/docs`**
on your running instance.

Interactive OpenAPI / Swagger documentation is also accessible at **`/api/docs/swagger`**.

## 📄 License

Licensed under the [Apache License, Version 2.0](LICENSE).
