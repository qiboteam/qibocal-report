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
# Serve current directory on port 8000
qibocal report serve

# Serve a specific folder on custom port
qibocal report serve ./sample_data --port 8080 --host 0.0.0.0
```

This command starts the FastAPI backend and serves the bundled web frontend. Open your browser at `http://127.0.0.1:8000` to interact with your reports.

### 2. Standalone Dashboard Mode

If you have one or multiple remote servers running across your lab network or cloud clusters, launch the dashboard alone:

```bash
qibocal report dashboard --port 8000
```

You can then add, name, and monitor all your remote servers from the centralized interface.

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
