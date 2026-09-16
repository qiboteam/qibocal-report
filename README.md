# Qibocal Report (`qibocal-report`)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10+-purple.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/frontend-Vue_3-42b883.svg)](https://vuejs.org/)

Modern, lightweight web application and server to serve, explore, and analyze [Qibocal](https://github.com/qiboteam/qibocal) calibration reports interactively.

Designed as an easily deployable alternative to static HTML pages, `qibocal-report` provides an interactive SPA frontend, a high-throughput FastAPI backend, a multi-server management dashboard, and instant print-to-PDF reports.

---

## ⚡ Quick Start

### 1. Installation

Install directly with `pip` or `uv`:

```bash
# In your Python environment
pip install .

# Or using uv
uv pip install .
```

### 2. Serving Reports (CLI)

Point to any directory containing Qibocal calibration folders:

```bash
# Serve the included sample calibration datasets
qibocal-report serve ./sample_data --port 8000

# Or serve your current lab directory
qibocal-report serve
```

Open your browser at `http://127.0.0.1:8000`.

### 3. Standalone Dashboard Mode

To monitor and connect to multiple remote Qibocal report servers across your network:

```bash
qibocal-report dashboard --port 8000
```

---

## 🌟 Key Features

- **Servers Management (Issue #4 & #11)**:
  - Central URL bar: paste and hit Enter to connect to a new server.
  - Auto-generated Docker-like names (e.g., `zen-bohr`, `calm-feynman`) and 10+ elegant abstract SVG avatars.
  - Interactive card list with status ping, report count, edit modal, and delete options.
  - Persistent server registry saved to `~/.config/qibocal-report/servers.json`.

- **Search & Discovery Dashboard (Issue #3)**:
  - Collapsible, vertically split sidebar.
  - Multi-faceted filters: Author, interactive timeline date histogram, protocol frequency checklist (sorted high-to-low), and labels search.
  - Dual visualization modes:
    - **Table View** (default): Sortable columns for compact browsing.
    - **Horizontal Card View**: Full-width cards (inspired by *Inspire-HEP*) with protocol chips and metadata.

- **Interactive Report Visualization (Issue #10 & #3)**:
  - Protocols summary sidebar with status badges and quick scroll-to links.
  - Injected protocol HTML tables and interactive Plotly.js figures.
  - **Pre-cached mode**: Reuses existing `report/` artifacts instantly without heavy Qibocal dependencies.
  - **On-the-fly mode**: Generates figures dynamically when not pre-cached.
  - **Regenerate Plots**: Single-click plot invalidation and re-computation.
  - **Print to PDF**: Isolated report layout (`@media print` CSS) tailored for clean PDF generation.

- **Aesthetics & Palette (Issue #2)**:
  - Modern, minimalist light theme inspired by *BackMarket*.
  - Monochromatic purple palette (`#833dff`, `#ebe0ff`, `#c8a8ff`, `#f7f7f7`).
  - Serif typography for primary headings (`h1`), clean sans-serif for body and subheadings.

- **Embedded Documentation (Issue #12)**:
  - Complete User Guide, Developer Architecture documentation, and REST API specification shipped inside the frontend reader and available via `/docs`.
  - Interactive OpenAPI Swagger UI at `/api/docs/swagger`.

---

## 🛠️ Development & Environment (devenv, uv, pnpm)

This repository uses [devenv](https://devenv.sh) for reproducible nix-based environments, [uv](https://docs.astral.sh/uv/) for Python packaging, and [pnpm](https://pnpm.io/) for frontend packages.

### Enter Development Shell

```bash
devenv shell
```

The shell provides:
- Python 3.12 (`languages.python`)
- `uv` package manager
- Node.js 22 & `pnpm`
- Pre-configured shell scripts

### Common Development Tasks

```bash
# Run backend test suite
devenv shell -- pytest tests/
# or: devenv test

# Build frontend and copy assets into Python package
devenv shell -- build-frontend

# Build standalone Python wheel
devenv shell -- uv build

# Serve sample data in development mode
devenv shell -- serve
```

### Running Frontend with Hot Module Replacement (HMR)

In one terminal:
```bash
devenv shell -- qibocal-report serve ./sample_data --reload
```
In another terminal:
```bash
cd frontend
pnpm dev
```
Open `http://localhost:5173` with instant Vite HMR proxying `/api` requests to port 8000.

---

## 📂 Project Structure

```
qibocal-report/
├── devenv.nix                     # Nix development environment configuration
├── devenv.yaml                    # Nixpkgs channel configuration
├── pyproject.toml                 # Python package and entry points
├── sample_data/                   # Realistic sample calibration runs (Spectroscopy, Rabi, Ramsey, RB)
├── docs/                          # Plain markdown documentation (usage, developer, api)
│   ├── usage.md
│   ├── developer.md
│   └── api.md
├── src/
│   └── qibocal_report/
│       ├── __init__.py
│       ├── cli.py                 # Click CLI commands (`serve`, `dashboard`)
│       ├── config.py              # Server registry & ~/.config persistence
│       ├── models.py              # Pydantic data schemas
│       ├── scanner.py             # Directory crawler and search facet indexing
│       ├── generator.py           # Pre-cached loader & on-the-fly protocol runner
│       ├── api.py                 # FastAPI REST application & SPA router
│       └── static/                # Bundled frontend assets & documentation
├── frontend/                      # Vue 3 + Vite + UnoCSS application
│   ├── index.html
│   ├── vite.config.js
│   ├── src/
│   │   ├── components/            # Sidebar, ServerCard, ServerModal, DateHistogram, etc.
│   │   ├── views/                 # ServersView, DashboardView, ReportView, DocsView
│   │   ├── store.js               # Reactive state & localStorage persistence
│   │   └── router.js              # Vue Router navigation
└── tests/
    └── test_backend.py            # Pytest test suite covering scanner, generator, API
```

---

## 📜 License

Licensed under the Apache License, Version 2.0.
