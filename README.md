<div align="center">

<img src="https://raw.githubusercontent.com/qiboteam/qibo/main/doc/source/_static/qibo_logo_dark.svg" alt="Qibo Logo" width="300" style="margin: 1.2rem 0;" />

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
- **Multi-Server Dashboard**: Connect to and manage local or remote report servers from one place.
- **Search & Filters**: Find calibration runs by title, platform, author, protocol, tag, or date.
- **Statistics Dashboard**: Follow calibration activity over time and explore trends across protocols, authors, and platforms.
- **Batch Actions**: Organize multiple runs at once by updating tags and authors, or deleting reports.

## 🚀 Quick Start

### 1. Installation

Install using `pip`:

```bash
pip install qibocal-report
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
qibocal notebook connect
qibocal notebook connect --ssh myuser@login -q mychip -w /shared/calibration
qibocal notebook connect --marimo --venv ./calibration-env -n
```

The command opens an authenticated local URL and stays attached until Ctrl+C.
Use `--marimo` for Marimo instead of JupyterLab, or `-n` to print the URL without
opening a browser. Save reusable connections with `qibocal notebook add`.

See **`man qibocal`** ([source](data/share/man/man1/qibocal.1)) for connection
management, environment setup, networking requirements, and configuration
examples, or `qibocal notebook connect --help` for command options.

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

## 📖 Documentation

The documentation covers report and server management, calibration results and
exports, development and architecture, and CLI and API references.
Select **Documentation** in the application's navigation, or open **`/#/docs`**
on your running instance.

Interactive OpenAPI / Swagger documentation is also accessible at **`/api/docs/swagger`**.

## 📄 License

Licensed under the [Apache License, Version 2.0](LICENSE).
