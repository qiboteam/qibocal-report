# Qibocal Report (`qibocal-report`)

<div align="center">

<img src="https://raw.githubusercontent.com/qiboteam/qibo/main/doc/source/_static/qibo_logo_dark.svg" alt="Qibo Logo" width="300" style="margin: 1.2rem 0;" />

**Modern, lightweight web application and high-throughput server to explore, analyze, and manage [Qibocal](https://github.com/qiboteam/qibocal) calibration reports interactively.**

[![Python](https://img.shields.io/badge/python-3.10+-purple.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/frontend-Vue_3-42b883.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Website](https://img.shields.io/badge/website-qibo.science-833dff.svg)](https://qibo.science)

</div>

---

## 🌐 The Qibo Ecosystem

`qibocal-report` is part of the **[Qibo](https://qibo.science)** open-source quantum computing ecosystem:

| Project | Description | Link |
| :--- | :--- | :--- |
| **Qibo** | Full-stack quantum simulation and algorithms framework. | [qibo.science/qibo](https://qibo.science/qibo/stable/) • [GitHub](https://github.com/qiboteam/qibo) |
| **Qibolab** | Dedicated quantum hardware control and pulse execution layer. | [qibo.science/qibolab](https://qibo.science/qibolab/stable/) • [GitHub](https://github.com/qiboteam/qibolab) |
| **Qibocal** | Protocols for characterization, calibration, and validation of quantum processors. | [qibo.science/qibocal](https://qibo.science/qibocal/stable/) • [GitHub](https://github.com/qiboteam/qibocal) |
| **Qibocal Report** | Modern web app and server to explore, compare, and manage Qibocal calibration runs. | [qibocal-report Docs](#-documentation) • [GitHub](https://github.com/qiboteam/qibocal-report) |

---

## ⚡ Key Features

- **Interactive Visualizations**: High-resolution 2D and 3D graphics powered by **Plotly.js** with zoom, pan, hover data inspection, and image export.
- **Multi-Server Dashboard**: Connect to, name, and monitor multiple local or remote Qibocal report servers across your lab network; auto-assigned Docker-style names and abstract geometric avatars, with persistent storage in `$XDG_CONFIG_HOME/qibocal-report/servers.json` (fallback: `~/.config/qibocal-report/servers.json`).
- **Search & Smart Facets**: Instant full-text search across titles, platforms, authors, protocols, and tags; faceted filtering with author filters, protocol frequency ranking, interactive date histogram timeline, and tag search.
- **Dual Display Modes**: Toggle seamlessly between sortable, resizable **Table View** and rich **Card View** (inspired by Inspire-HEP full-width cards).
- **Statistics Dashboard**: Dedicated analytics view (`/#/statistics`) tracking calibration throughput, activity over time, protocol frequency distribution, author activity, and platform breakdowns.
- **Batch Actions**: Bulk tag, update author, or safely delete multiple calibration runs simultaneously from the dashboard.
- **Detailed Protocol Cards**:
  - Individual routine duration extracted directly from `meta.json`.
  - Injected protocol summary tables styled natively to match the application aesthetic.
  - One-click individual protocol data zip downloads.
- **Instant On-The-Fly Downloads**:
  - Full report folder as `.zip`.
  - Calibrated platform configuration folder (`new_platform/`) as `.zip` (sparkled chip icon).
  - Initial platform configuration folder (`platform/`) as `.zip` (plain chip icon).
  - Protocol-level data folder as `.zip`.
  - Direct browser viewing of `meta.json` (`{}`).
- **On-The-Fly Regeneration**: Recompute and refresh protocol figures dynamically via backend evaluation routines.
- **Publication-Grade Print to PDF**: Dedicated print media stylesheets that cleanly format tables and charts while hiding navigation and controls for archival PDF exports.

---

## 🚀 Quick Start

### 1. Installation

Install directly using `pip` or `uv`:

```bash
# Using pip
pip install qibocal-report

# Or using uv
uv pip install qibocal-report
```

### 2. Serving Reports (CLI)

Point `qibocal report server` to any directory containing Qibocal calibration runs:

```bash
# Start backend server and embedded web app
qibocal report server ./sample_data --port 8000
```

Open your browser at **`http://localhost:8000`**.

### Interactive Notebooks

Start JupyterLab locally, over SSH, or on a SLURM partition:

```bash
qibocal notebook
qibocal notebook --ssh myuser@login -q mychip -w /shared/calibration
qibocal notebook --marimo --venv ./calibration-env -n
```

The command opens an authenticated local URL and stays attached until Ctrl+C.
Each worker logs its node identity to stderr as soon as it starts: the actual
hostname, fully qualified domain name, user, OS release, architecture, Python
executable/version, process ID, and working directory on arrival. SLURM sessions
log the access and compute nodes separately, including available allocation
details (cluster, job/step IDs, partition, node lists, CPU/memory, and GPU IDs).
Without SLURM, the same node serves both roles.
Rich renders these details as labeled node panels, with colored startup stages
and a clear ready banner. Rendering happens locally: SSH and SLURM workers use
only Python's standard library and forward structured diagnostics, so they do
not need Rich installed or a remote terminal. Redirected output remains readable
without ANSI colors; the authenticated URL stays on its own line on stdout.
Use `-n` to print the URL without opening a browser. Notebook connections can
be named in `~/.config/qibocal-report/notebooks.json` (or under
`$XDG_CONFIG_HOME`) and invoked with `qibocal notebook myconnection`.
Existing kernel environments remain unchanged; missing ones are created empty.
Named environments live under `$XDG_CACHE_HOME/qibocal/envs/` (fallback:
`~/.cache/qibocal/envs/`). Server dependencies are installed separately on first use.

Notebook dispatch is documented outside the web frontend in the installed
**`man qibocal`** page ([source](data/share/man/man1/qibocal.1)), including networking
requirements, environment paths, and configuration examples.

### 3. Standalone Client Mode

To monitor and manage multiple remote report servers across your lab network from your workstation:

```bash
qibocal report client --port 8000
```

### 4. Developer Mode (Live HMR)

For developers modifying the frontend or backend:

```bash
qibocal report dev ./sample_data
```

Starts the FastAPI backend with auto-reload and the Vite frontend dev server at `http://localhost:5173` with instant Hot Module Replacement.

### 5. Static Export & GitHub Pages Deployment

The frontend can be exported as a standalone static Single Page Application (SPA) for static hosts such as **GitHub Pages**. Because GitHub Pages serves static files, only the frontend is deployed; backend instances run independently on your lab servers or cloud infrastructure and connect directly via the web interface:

```bash
# Export static bundle via CLI
qibocal report export ./dist

# Or build directly with pnpm
cd frontend && pnpm run build
```

Automated deployment to GitHub Pages is configured via [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml).

---

## 📖 Documentation

Comprehensive documentation is available directly within the running web application at **`/#/docs`** and organized in sections and subpages:

- **Overview & Qibo Ecosystem** (`docs/index.md`)
- **User Guide**:
  - [Quickstart & Directory Layout](docs/user-guide/quickstart.md)
  - [Dashboard & Server Management](docs/user-guide/dashboard.md)
  - [Reports, Protocols & Exports](docs/user-guide/reports.md)
- **Developer & Architecture**:
  - [System Architecture](docs/developer/architecture.md)
  - [Development Workflow](docs/developer/workflow.md)
  - [Design System & Aesthetics](docs/developer/design-system.md)
- **Reference**:
  - [CLI Reference](docs/reference/cli.md)
  - [REST API & WebSockets](docs/reference/api.md)

Interactive OpenAPI / Swagger documentation is also accessible at **`/api/docs/swagger`**.

---

## 🛠️ Development & Environment (`devenv`, `uv`, `pnpm`)

This repository uses [devenv](https://devenv.sh) for reproducible nix-based environments:

```bash
# Enter development shell
devenv shell

# Run pytest backend test suite
devenv shell -- pytest tests/

# Build frontend and embed into Python package
devenv shell -- build-frontend

# Build frontend static export for static web hosting
devenv shell -- export-static

# Build standalone Python wheel
devenv shell -- build-wheel

# Run pre-commit hooks and linters
devenv shell -- prek run --all-files
```

---

## 📄 License

Licensed under the [Apache License, Version 2.0](LICENSE).
