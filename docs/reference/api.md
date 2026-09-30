# Reference: REST API & WebSockets

The `qibocal-report` backend exposes a fully typed OpenAPI 3.1 REST API along with real-time WebSocket capabilities.

Interactive Swagger documentation is available at **`/api/docs/swagger`**, and the raw OpenAPI specification is available at **`/api/openapi.json`**.

---

## 🩺 Health & Server Diagnostics

### `GET /api/health`
Returns system status, active server identifier, report count, and scanned root directory.

#### Response Example
```json
{
  "status": "ok",
  "server_name": "local-sample_data",
  "reports_count": 4,
  "root_dir": "/path/to/sample_data"
}
```

---

## 🌐 Server Registry Management

These endpoints manage the backend's configuration file, independently of the
browser-local registry displayed on `/servers`. The client does not synchronize
its server list with these endpoints.

### `GET /api/servers`
List all registered local and remote report servers.

### `POST /api/servers`
Register a new remote server.
- **Body**: `{"url": "http://192.168.1.50:8000", "name": "Lab-Rig-A", "description": "Dilution Fridge A"}`

### `PUT /api/servers/{server_id}`
Update an existing server's metadata, display name, avatar, or default status.

### `DELETE /api/servers/{server_id}`
Remove a server from the local registry.

### `POST /api/servers/save`
Explicitly save the backend registry to `~/.config/qibocal-report/servers.json`.
Registry mutations already save this file automatically.

---

## 📑 Reports & Filtering

### `GET /api/reports`
Retrieve a paginated, filtered list of calibration reports.

#### Query Parameters
- `q`: Free-text search matching title, platform, author, or tags.
- `author`: Filter by author handle.
- `protocol`: Filter by executed routine name.
- `label`: Filter by custom tag/label.
- `start_date`, `end_date`: Filter by date range (`YYYY-MM-DD`).
- `sort_by`: Sorting order (`date_desc`, `date_asc`, `title`).

### `GET /api/reports/stats`
Returns aggregated statistical distributions across all discovered reports:
- `authors`: Unique authors list.
- `labels`: Unique tags list.
- `protocols`: Array of `{ name, count }` sorted by frequency descending.
- `platforms`: Platform distribution.
- `date_histogram`: Array of `{ date, count }` chronologically ordered.

### `GET /api/reports/{report_id}`
Retrieve detailed metadata, platform snapshots, history, and protocol summaries for a single report.

---

## 🔬 Protocol Outputs & Regeneration

### `GET /api/reports/{report_id}/protocols`
Fetch all protocol outputs including formatted HTML tables and serialized Plotly figure structures.

### `POST /api/reports/{report_id}/regenerate`
Purge the cached `report/` folder for this run and recompute figures on the fly using Qibocal evaluation routines.

---

## 💾 On-the-Fly Downloads & Meta

### `GET /api/reports/{report_id}/download/full`
Streams the entire calibration run directory as a compressed `.zip` archive.

### `GET /api/reports/{report_id}/download/new-platform`
Streams the calibrated `new_platform/` configuration directory as a `.zip` archive.

### `GET /api/reports/{report_id}/download/old-platform`
Streams the initial `platform/` configuration directory as a `.zip` archive.

### `GET /api/reports/{report_id}/download/data/{protocol_id}`
Streams the data directory for a specific protocol routine as a `.zip` archive.

### `GET /api/reports/{report_id}/meta.json`
Returns `meta.json` directly as an inline `application/json` payload for browser inspection.

---

## ⚡ Bulk & Report Actions

### `POST /api/reports/bulk-action`
Executes batch operations across multiple reports.

#### Payload Schema
```json
{
  "action": "label", // "label" | "unlabel" | "author" | "delete"
  "report_ids": ["10:50:56_[0]_resonator_punchout", "21:47:29_[3]_pi-pulse"],
  "label": "verified",
  "author": "new_author"
}
```

### `POST /api/reports/{report_id}/label`
Add a label/tag to a single report.

### `DELETE /api/reports/{report_id}/label/{label_name}`
Remove a label/tag from a single report.

### `PUT /api/reports/{report_id}/author`
Update the author handle for a single report.

### `DELETE /api/reports/{report_id}`
Delete a single report directory from disk.

---

## 🔌 WebSockets

### `WS /ws/reports/{report_id}`
Connect to receive real-time execution events, streaming status changes, and progress updates.

---

## 📖 Documentation Content

### `GET /api/docs-content/{doc_name}`
Serve raw markdown documentation content for the in-app documentation reader.

### `GET /api/docs-nav`
Returns the structured documentation navigation tree (sections, pages, and titles).
