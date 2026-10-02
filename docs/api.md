# REST API Specification

The `qibocal-report` backend exposes a fully documented OpenAPI REST API. Interactive Swagger documentation is accessible at **`/api/docs/swagger`**.

> **Tip:** Complete endpoint details, schemas, and WebSocket documentation are available in **[Reference: REST API & WebSockets](reference/api.md)** and **[Reference: CLI](reference/cli.md)**.

---

## Summary of Endpoints

### 🩺 Health & Diagnostics
- `GET /api/health` - Check server health, discovered report count, and scanned directory.

### 🌐 Server Registry Management
- `GET /api/servers` - List all registered servers.
- `POST /api/servers` - Register a new remote server.
- `PUT /api/servers/{id}` - Modify server parameters.
- `DELETE /api/servers/{id}` - Remove server registration.
- `POST /api/servers/save` - Persist server list to `$XDG_CONFIG_HOME/qibocal-report/servers.json` (fallback: `~/.config/qibocal-report/servers.json`; overridden by `QIBOCAL_REPORT_CONFIG_DIR`).

### 📑 Reports & Search
- `GET /api/reports` - List and filter reports with query parameters (`q`, `author`, `protocol`, `label`, `start_date`, `end_date`, `sort_by`).
- `GET /api/reports/stats` - Aggregated facet counts (authors, labels, protocols, platforms, date histogram).
- `GET /api/reports/{report_id}` - Metadata, platform snapshot, history, and protocols summary.
- `GET /api/reports/{report_id}/protocols` - Protocol outputs (HTML tables, Plotly figures).
- `POST /api/reports/{report_id}/regenerate` - Purge cached figures and recompute on the fly.

### 💾 On-The-Fly Downloads & Inspection
- `GET /api/reports/{report_id}/download/full` - Download full report folder as `.zip`.
- `GET /api/reports/{report_id}/download/new-platform` - Download calibrated platform folder as `.zip`.
- `GET /api/reports/{report_id}/download/old-platform` - Download initial platform folder as `.zip`.
- `GET /api/reports/{report_id}/download/data/{protocol_id}` - Download specific protocol data folder as `.zip`.
- `GET /api/reports/{report_id}/meta.json` - Inspect raw `meta.json` directly in the browser.

### ⚡ Actions & WebSockets
- `POST /api/reports/bulk-action` - Bulk tag, author assignment, or deletion.
- `POST /api/reports/{report_id}/label` / `DELETE /api/reports/{report_id}/label/{label}` - Manage single report tags.
- `PUT /api/reports/{report_id}/author` - Update single report author.
- `DELETE /api/reports/{report_id}` - Delete a single report directory.
- `WS /ws/reports/{report_id}` - WebSocket for real-time calibration updates.

### 📖 Documentation Content
- `GET /api/docs-content/{doc_name:path}` - Serve markdown documentation.
- `GET /api/docs-nav` - Return structured documentation navigation tree.
