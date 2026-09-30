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

On authentication-enabled servers, these actions use your sign-in session,
including for remote instances. Protocol-data, platform, and archive downloads
use the same authenticated requests. If your browser blocks the metadata tab,
allow pop-ups for the report application and try again.

---

## 🔄 On-The-Fly Regeneration

If a calibration routine needs to be re-plotted with updated fitting criteria or if cache invalidation is required:

- Click the **Regenerate** button in the report header card.
- The server purges the cached `report/` folder and re-runs evaluation routines.
- Updated plots and parameters are automatically refreshed in your browser without requiring a server restart.

### Installing or switching Qibocal

Both the dashboard plot preview and the full report explicitly show generation
errors, including when Qibocal is not installed on the report server.
Pre-cached plots remain viewable without Qibocal.

On an authentication-enabled server, signed-in administrators can use
**Install Qibocal** or **Switch Qibocal Version** in either view. The picker
offers a few recent compatible stable PyPI releases and the latest default
branch of the official [Git repository](https://github.com/qiboteam/qibocal).
The current server version is shown in the picker. If PyPI is unavailable, the
error is displayed and the Git option remains available.

**Install and Regenerate** changes Qibocal and its dependencies in the server's
Python environment for all users, then regenerates the current report's cached
plots. Other reports' cached plots are not changed; use **Regenerate Plots** to
refresh them when needed. Future plot generation uses the installed version
without a server restart. Viewers, editors, and open (unauthenticated) servers
cannot install or switch versions through the application.

---

## 🖨️ Publication-Grade Print to PDF

To generate an archival PDF report or print a hard copy:

1. Click the **Print to PDF** button in the top action bar (or press `Cmd+P` / `Ctrl+P`).
2. The print media stylesheet automatically:
   - Hides the sidebar, search inputs, and interactive UI buttons.
   - Preserves full report header details and hardware metadata.
   - Formats Plotly charts and protocol tables for crisp printing.
   - Manages smart page breaks between protocol cards to prevent awkward mid-table cuts.
