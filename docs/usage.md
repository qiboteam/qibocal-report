# User Guide

`qibocal-report` is a modern, lightweight web application and server designed to serve and explore Qibocal calibration reports interactively.

## 🚀 Quick Start

### Installation

Install the package directly using `pip` or `uv`:

```bash
# Using pip
pip install qibocal-report

# Or using uv
uv pip install qibocal-report
```

### 1. Serving Reports from a Directory

Point `qibocal` to any directory containing Qibocal calibration outputs (e.g. current directory or a designated calibration archive):

```bash
# Start the FastAPI backend server
qibocal report server ./sample_data --port 8000

# Or serve both backend and bundled frontend together
qibocal report serve ./sample_data --port 8000
```

### 2. Standalone Client Mode

If you have one or multiple remote servers running across your lab network or cloud clusters, launch the client alone:

```bash
qibocal report client --port 8000
```

You can then add, name, and monitor all your remote servers from the centralized interface.

### 3. Developer Mode (Live HMR)

To run the backend with the frontend Vite development server for live Hot Module Replacement:

```bash
qibocal report dev ./sample_data
```

---

## 🖥️ Key Features & Workflow

### 📡 Server Management
- **One-click Server Registration**: In the *Servers* view, paste any report server URL and press **Enter**.
- **Auto-generated Names & Avatars**: Servers are automatically assigned a memorable Docker-like name (e.g., `zen-bohr`, `calm-feynman`) and an abstract geometric avatar.
- **Customization**: Use the 3-dots menu on any server card to edit its name, description, avatar, or URL.
- **Persistent Configuration**: Click the **Save to Configuration** button to store your registered servers in `~/.config/qibocal-report/servers.json`.

### 🔍 Search & Filtering Dashboard
- **Instant Search**: Full-text search across report titles, platform names, authors, protocols, and labels.
- **Smart Facets**:
  - **Author**: Filter runs by calibration scientist.
  - **Date Range & Histogram**: Interactive timeline distribution showing experiment activity over time.
  - **Protocol Suggestions**: Protocol checkboxes ordered from most frequent to least frequent for quick selection.
  - **Labels**: Tag-based filtering with label search.
- **Dual Visualizations**: Toggle between standard **Table View** and rich **Card View** (inspired by Inspire-HEP full-width cards).

### 📊 Interactive Report Visualization
- **Protocol Summaries**: Sidebar navigator lists all executed routines with their status and execution durations.
- **Plotly.js Interactive Graphics**: Zoom, pan, inspect data points, and download high-resolution plots directly in the browser.
- **Platform Snapshots**: Inspect hardware configurations and qubit parameters associated with the calibration run.
- **Regenerate Plots**: Trigger on-the-fly re-computation and cache invalidation via the **Regenerate** button.
- **Print to PDF**: Click **Print to PDF** for a publication-ready document layout with automatic isolation of report content.
