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

The Python package is the server alone: headless, without the dashboard, which is deployed from `frontend/` to GitHub Pages by `.github/workflows/deploy.yml` and embedded in the desktop launcher — one build of the pages, in two places, rather than a third copy in every wheel.

```bash
# The wheel, with uv
devenv shell -- build-wheel
# or: uv build
```

---

## 🏷️ Versions & Releases

There is one version, the Python package's, in `pyproject.toml`, in [PEP 440](https://peps.python.org/pep-0440/) form: `0.1.0a1` for an alpha, `0.1.0b1`, `0.1.0rc1`, then `0.1.0`. The package, `qibocal --version` and the API all read it from the installed metadata. The servers' `GET /api/version` answers it, along with the API version, which counts the API's breaking changes; see the [API reference](../reference/api.md).

A release is a GitHub release whose tag is that version prefixed with `v` — `v0.1.0a1`. Its launcher workflow refuses a tag that does not match `pyproject.toml`, and gives the desktop application the same version in the form its installers accept: SemVer with a numeric pre-release, alphas counted from 1, betas from 101 and release candidates from 201, so `0.1.0a1` is `0.1.0-1`, `0.1.0rc2` is `0.1.0-202`, and `0.1.0` is greater than all of them. The installers are attached to the release. Bump `pyproject.toml` for the next version right after tagging.
