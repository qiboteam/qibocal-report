# User Guide: Reports, Protocols & Exports

Selecting any calibration run from the dashboard opens the dedicated **Report View** (`/#/reports/{id}`), providing a deep dive into experimental measurements, fitted parameters, and hardware snapshots.

---

## 🧭 Navigation & Sidebar

The left-hand sidebar serves as a quick navigator across all executed routines in the report:

- **Protocol Status Badges**: Quickly see which protocols succeeded (green checkmark) or experienced warnings/failures.
- **Execution Timings**: Review the duration of each individual routine alongside total experiment runtime.
- **Quick Jumping**: Click any protocol in the list to scroll smoothly to its corresponding card.
- **Collapsible Sidebar**: Click the toggle chevron at the bottom of the sidebar to collapse it to compact icon mode, maximizing screen real estate for charts.

---

## 📊 Protocol Cards & Visualizations

Each protocol routine is presented in an individual card:

### 1. Interactive Plotly Charts
- Interactive 2D and 3D graphics powered by **Plotly.js**.
- **Zoom & Pan**: Click and drag to box-zoom into resonance peaks, Rabi oscillations, or Ramsey fringes. Double-click to reset zoom.
- **Hover Inspection**: Move your cursor across data points to inspect exact frequencies, amplitudes, phases, and error bars.
- **Snapshot Export**: Use the camera icon in the Plotly toolbar to export publication-quality PNG images.

### 2. Formatted Results Tables
- Injected protocol summary tables displaying fitted parameters ($f_{01}$, $\pi$-pulse amplitude, $T_1$, $T_2^*$, readout fidelity).
- Styled natively with clean borders, monochromatic purple headers, and typography aligned with the application theme.

### 3. Direct Protocol Data Download
- Each protocol card includes an individual **Download Protocol Data (.zip)** button in its header.
- Compresses and downloads only the data directory associated with that specific routine for rapid offline analysis in Python or Jupyter.

---

## 💾 On-The-Fly ZIP Downloads & Inspection

The sidebar includes instant download actions generated dynamically on the fly:

| Button / Icon | Description | Endpoint |
| :--- | :--- | :--- |
| **Download Protocol (.zip)** | Full archive containing all data, logs, platform snapshots, and cached figures. | `GET /api/reports/{id}/download/full` |
| **New Platform (.zip)** *(Sparkled chip)* | Calibrated hardware parameters resulting from the run, packaged as a platform folder. | `GET /api/reports/{id}/download/new-platform` |
| **Old Platform (.zip)** *(Plain chip)* | Initial pre-calibration hardware parameters used at the start of the experiment. | `GET /api/reports/{id}/download/old-platform` |
| **Meta.json (`{}`)** | View raw execution metadata inline in a new browser tab. | `GET /api/reports/{id}/meta.json` |

---

## 🔄 On-The-Fly Regeneration

If a calibration routine needs to be re-plotted with updated fitting criteria or if cache invalidation is required:

- Click the **Regenerate** button in the report header card.
- The server purges the cached `report/` folder and re-runs evaluation routines.
- Updated plots and parameters are automatically refreshed in your browser without requiring a server restart.

---

## 🖨️ Publication-Grade Print to PDF

To generate an archival PDF report or print a hard copy:

1. Click the **Print to PDF** button in the top action bar (or press `Cmd+P` / `Ctrl+P`).
2. The print media stylesheet automatically:
   - Hides the sidebar, search inputs, and interactive UI buttons.
   - Preserves full report header details and hardware metadata.
   - Formats Plotly charts and protocol tables for crisp printing.
   - Manages smart page breaks between protocol cards to prevent awkward mid-table cuts.
