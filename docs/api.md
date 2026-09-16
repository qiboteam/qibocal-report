# REST API Specification

The `qibocal-report` backend exposes a fully documented OpenAPI REST API. Interactive Swagger documentation is accessible at `/api/docs/swagger`.

## Summary of Endpoints

### 🩺 Health & Diagnostics
- `GET /api/health`
  - Returns server status, server name, total reports discovered, and the root scanning directory.
  - Response:
    ```json
    {
      "status": "ok",
      "server_name": "local-instance",
      "reports_count": 3,
      "root_dir": "/path/to/sample_data"
    }
    ```

---

### 🌐 Server Registry Management
- `GET /api/servers`
  - List all registered remote and local servers.
- `POST /api/servers`
  - Register a new server URL.
  - Body: `{"url": "http://192.168.1.100:8000", "name": "Optional Name"}`
- `PUT /api/servers/{id}`
  - Modify server parameters (name, description, avatar, default flag).
- `DELETE /api/servers/{id}`
  - Remove server registration.
- `POST /api/servers/save`
  - Persist current server list to `~/.config/qibocal-report/servers.json`.

---

### 📑 Reports & Search
- `GET /api/reports`
  - List and filter reports.
  - Query parameters:
    - `q`: Free-text search across titles, platforms, protocols, authors.
    - `author`: Filter by author username.
    - `protocol`: Filter by protocol routine name.
    - `label`: Filter by label tags.
    - `start_date`, `end_date`: Date range filter (`YYYY-MM-DD`).
    - `sort_by`: `date_desc`, `date_asc`, `title`.
- `GET /api/reports/stats`
  - Returns aggregation facets:
    - `authors`: Array of unique authors.
    - `labels`: Array of unique labels.
    - `protocols`: Array of `{ name, count }` sorted descending by frequency.
    - `date_histogram`: Array of `{ date, count }` chronologically ordered.
- `GET /api/reports/{report_id}`
  - Returns metadata, platform snapshot, history, and protocols summary.
- `GET /api/reports/{report_id}/protocols`
  - Returns all protocol details including rendered HTML tables and Plotly figure JSON structures.
- `POST /api/reports/{report_id}/regenerate`
  - Deletes cached `report/` folder and regenerates plots on-the-fly.

---

### 📖 Documentation Content
- `GET /api/docs-content/{doc_name}`
  - Fetches raw markdown documentation (`usage`, `developer`, `api`) to render inside the frontend reader.
