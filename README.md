# Qibocal Report (`qibocal-report`)

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
qibocal report serve ./sample_data --port 8000

# Or serve your current lab directory
qibocal report serve
```

Open your browser at `http://127.0.0.1:8000`.

### 3. Standalone Dashboard Mode

To monitor and connect to multiple remote Qibocal report servers across your network:

```bash
qibocal report dashboard --port 8000
```

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
devenv shell -- qibocal report serve ./sample_data --reload
```

In another terminal:

```bash
cd frontend
pnpm dev
```

Open `http://localhost:5173` with instant Vite HMR proxying `/api` requests to port 8000.
