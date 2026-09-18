# Developer: System Architecture

`qibocal-report` is engineered as a decoupled, modular system composed of a high-throughput **FastAPI** backend and a reactive **Vue 3** Single-Page Application (SPA).

```
┌────────────────────────────────────────────────────────┐
│                   Vue 3 SPA Frontend                   │
│   (Vite, UnoCSS, Plotly.js, Vue Router, Pinia-like)    │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP REST / WebSockets
┌──────────────────────────▼─────────────────────────────┐
│                  FastAPI Backend Server                │
│             (Uvicorn, Pydantic v2, Python 3.10+)       │
└───────┬──────────────────┬──────────────────────┬──────┘
        │                  │                      │
┌───────▼──────┐    ┌──────▼──────┐       ┌───────▼──────┐
│  Directory   │    │  Generator  │       │  In-Memory   │
│   Scanner    │    │ & Evaluator │       │    Cache     │
│ (scanner.py) │    │(generator.py)│       │  & Streams   │
└──────────────┘    └─────────────┘       └──────────────┘
```

---

## 🐍 Backend Architecture (`src/qibocal_report/`)

### 1. Web Framework: FastAPI & Uvicorn
- Built on **FastAPI** for native asynchronous I/O, automatic OpenAPI 3.1 / Swagger generation, and dependency injection.
- Served in production using **Uvicorn**.

### 2. Strict Typing with Pydantic v2
- All payload structures, metadata representations, and protocol outputs are modeled with **Pydantic v2** (`BaseModel`), guaranteeing contract validation and high serialization speeds.

### 3. Report Scanner (`scanner.py`)
- Traverses the directory tree configured via `QIBOCAL_REPORT_DIR` or the CLI argument.
- Scans for directories containing `meta.json`.
- Extracts runcards, platform snapshots (`platform/`, `new_platform/`), executed protocols, qubit sets, and execution timestamps.
- Aggregates facets on the fly for lightning-fast statistical querying.

### 4. Report Generator & Evaluator (`generator.py`)
Provides two distinct operational modes:
- **Pre-cached Mode (Default)**:
  - If a calibration folder contains a `report/` subdirectory, the server reads the serialized Plotly JSON figures and HTML tables directly from disk.
  - **Zero Heavy Numerical Dependencies**: In this mode, `qibocal`, `qibo`, and numerical simulation backends do not need to be installed.
- **On-the-Fly Mode**:
  - When `report/` is absent, the backend evaluates the protocol routines dynamically.
  - If `qibocal` is available in the environment, its `.report()` methods are invoked to generate authentic figures.
  - In non-Qibocal environments, a lightweight fallback parser synthesizes representative resonance, Rabi, and Ramsey response curves.

### 5. On-the-Fly Streaming ZIP Packaging
- Implements in-memory zip streaming (`StreamingResponse`) via Python's `zipfile` module.
- Compresses directories into `.zip` archives on demand without writing intermediate files to disk.

### 6. Real-Time WebSockets
- Provides a WebSocket endpoint (`/ws/reports/{report_id}`) for live progress updates during active calibration runs.

---

## 🎨 Frontend Architecture (`frontend/`)

### 1. Vue 3 & Composition API
- Built with **Vue 3** utilizing the Composition API (`<script setup>`).
- Client-side routing managed by **Vue Router** with hash history mode (`createWebHashHistory`).

### 2. Build Pipeline: Vite
- Optimized bundling via **Vite 5**.
- Supports instant Hot Module Replacement (HMR) in development mode.

### 3. Styling Engine: UnoCSS
- Instant, atomic CSS generation using **UnoCSS** (`presetUno`, `presetAttributify`).
- Custom theme configuration reflecting the project's signature monochromatic purple aesthetic.

### 4. Charting: Plotly.js
- Visualizations rendered client-side using `plotly.js-dist-min`.
- Fully responsive containers with automatic layout recalculation on sidebar collapse or window resize.
