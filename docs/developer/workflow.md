# Developer: Development Workflow

This guide details the local setup, tooling, testing routines, and packaging pipeline for contributing to `qibocal-report`.

---

## 🛠️ Reproducible Environment (`devenv`, `uv`, `pnpm`)

The project uses [devenv.sh](https://devenv.sh) to configure a hermetic, reproducible developer environment backed by Nix.

### 1. Activating the Environment

```bash
# Enter development shell
devenv shell
```

The shell provides:
- **Python 3.12** with `uv` package manager
- **Node.js 22** with `pnpm`
- **Pre-commit validation tools** via `prek`

---

## ⚡ Developer Mode with Live HMR

To develop both frontend and backend concurrently:

```bash
# Start backend on :8000 and Vite dev server on :5173 with HMR
qibocal report dev ./sample_data
```

- Any modifications in `frontend/src/` trigger instant Hot Module Replacement without reloading the page.
- Requests to `/api` from Vite are automatically proxied to the running backend on port 8000.
- Changes in Python files reload the FastAPI server automatically via Uvicorn reload.

---

## 🧪 Testing Suite

### Running Backend Unit & Integration Tests

```bash
# Run pytest directly
pytest tests/

# Or via devenv shell
devenv shell -- pytest tests/
```

Test coverage includes:
- Health check and server discovery endpoints
- Report scanning, metadata parsing, and facet generation
- On-the-fly zip packaging (full, platform, and protocol data)
- In-browser `meta.json` serving
- Dynamic plot regeneration and error handling
- Markdown documentation serving endpoints

---

## 🎨 Code Quality & Linting (`prek`)

Pre-commit hooks are configured via `prek.toml` and run automatically on commit:

```bash
# Run all pre-commit checks across the repository
devenv shell -- prek run --all-files
```

Checks enforce:
- Python code formatting and linting via **Ruff**
- Python 3.11+ syntax upgrades via **pyupgrade**
- JSON / TOML validation
- Trailing whitespace removal and EOF formatting

---

## 📦 Building & Packaging

`qibocal-report` bundles the compiled Vue frontend inside the Python wheel distribution (`src/qibocal_report/static/`) so users can install and run the complete app with a single `pip install`:

```bash
# 1. Build frontend and copy assets into Python package static directory
devenv shell -- build-frontend

# 2. Build standalone Python wheel using uv
devenv shell -- build-wheel
# or: uv build
```
