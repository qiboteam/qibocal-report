# Developer Documentation & Architecture

`qibocal-report` is designed as a standalone, modular package providing both a high-performance backend and a clean, responsive single-page application (SPA).

## 🏗️ Architectural Overview

The project is structured into two main components:

1. **Python Backend (`src/qibocal_report/`)**:
   - Built on **FastAPI** for high throughput, asynchronous I/O, and native OpenAPI generation.
   - Built with **Pydantic v2** models for strict schema validation.
   - Self-contained packaging via native `uv_build` and `uv`.
   - Embeds the compiled SPA into `src/qibocal_report/static/` so that `pip install` yields a zero-dependency web application.

2. **Frontend Application (`frontend/`)**:
   - Built on **Vue 3** (Composition API, `<script setup>`).
   - Bundled with **Vite** for fast HMR and optimized builds.
   - Styled with **UnoCSS** utilizing a monochromatic purple palette inspired by *BackMarket* aesthetics.
   - Interactive charting powered by **Plotly.js**.

---

## ⚡ Execution Modes (Issue #10)

`qibocal-report` provides two complementary report consumption modes:

### 1. Pre-cached Mode (Default)
- If a run directory contains a `report/` subfolder with serialized JSON outputs, the server serves these artifacts directly.
- **Zero Python heavy dependencies**: In pre-cached mode, the server does not import `qibocal`, `qibo`, or numerical simulation libraries, guaranteeing instantaneous load times and immunity to Qibocal version drift.

### 2. On-the-Fly Mode
- If `report/` does not exist:
  - When `qibocal` is installed in the Python environment, the server calls the protocol's `.report()` routines, serializes the generated HTML tables and Plotly figures into JSON, and caches them inside `report/`.
  - When running in an environment without `qibocal` (or for mock runs), a lightweight synthetic protocol parser generates calibrated Lorentzian fits, Rabi oscillations, and Ramsey decay curves.
- Users can trigger an explicit refresh via `POST /api/reports/{id}/regenerate`, which purges `report/` and regenerates fresh figures.

---

## 🎨 Aesthetics & Styling (Issue #2)

The application follows the design specifications defined in Issue #2:
- **Palette**:
  - Main Background: `#f7f7f7` (very pale gray)
  - Element Background: `#ffffff` (pure white)
  - Light Accent: `#ebe0ff` (subtle highlight)
  - Mild Accent: `#c8a8ff` (borders and badges)
  - Primary Accent: `#833dff` (buttons and active selections)
  - Base Text: `#000000`
  - Subtle Muted: `#4a4a4a`
- **Typography**: Serif typeface for `h1` headings for an editorial, elegant look, and clean sans-serif for `h2+` and body text.
- **Shadows**: Soft, multi-layered shadows with subtle purple undertones instead of harsh borders.

---

## 🛠️ Environment & Development Workflow

The environment is reproducibly managed via **devenv**:

```bash
# Enter devenv shell (activates uv, python 3.12, node 24, pnpm)
devenv shell

# Run backend tests
pytest tests/

# Build frontend and bundle into Python package
cd frontend
pnpm install
pnpm build
cp -r dist/* ../src/qibocal_report/static/
```
