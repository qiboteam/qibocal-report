# Reference: REST API & WebSockets

The `qibocal-report` backend exposes a fully typed OpenAPI 3.1 REST API along with real-time WebSocket capabilities.

Interactive Swagger documentation is available at **`/api/docs/swagger`**, and the raw OpenAPI specification is available at **`/api/openapi.json`**.

---

## 🩺 Health & Server Diagnostics

### `GET /api/admin/logs?after=0`
Requires authentication to be enabled and a signed-in administrator (the same
strict authorization as Qibocal environment administration). Returns bounded
in-memory server log history with ANSI color escapes preserved:

```json
{"entries": [{"id": 1, "text": "\u001b[32mServer ready\u001b[0m\n"}], "cursor": 1}
```

Pass the last `cursor` as `after` to read newer entries. Logs include Rich
application messages and Python/uvicorn logging, and disappear on server
restart. Responses use `Cache-Control: no-store`.

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
Explicitly save the backend registry to
`$XDG_CONFIG_HOME/qibocal/servers.json` (fallback:
`~/.config/qibocal/servers.json`; overridden by `QIBOCAL_REPORT_CONFIG_DIR`).
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

Failed outputs have `status: "error"` and an informative `error` message. The
optional `error_code: "qibocal_not_installed"` identifies a genuinely missing
Qibocal installation. Missing dependencies, incompatible Qibocal APIs, invalid
report data, and individual routine failures retain their own error messages
without that code. Partial figures and tables remain available when a routine
fails for some targets.

### `POST /api/reports/{report_id}/regenerate`
Purge the cached `report/` folder for this run and recompute figures on the fly using Qibocal evaluation routines.

Generation uses a fresh process in the server's Python environment, with a
five-minute timeout, so subsequent requests use a newly installed Qibocal version
without restarting the server.

---

## 🧩 Qibocal Server Environment

### `GET /api/qibocal`
Inspect Qibocal's installed package metadata without importing its plotting
dependencies. Requires viewer access when authentication is enabled; it is also
available on open servers. Responses use `Cache-Control: no-store`.

```json
{"installed": true, "version": "0.2.7", "source": "pypi"}
```

If absent, `installed` is `false` and both `version` and `source` are `null`.
`source` is `"pypi"` or `"git"` for recognized installations, or `null` for an
unrecognized installation origin.

### `GET /api/admin/qibocal/options`
Requires authentication to be **enabled** and a logged-in user whose current
role is **admin**. The synthetic administrator on an authentication-disabled
server cannot access environment administration.

Returns the same installed status plus up to five recent stable, non-yanked
PyPI releases compatible with the server's Python version, plus the latest
compatible release from the previous major line if not already included.
For 0.x releases, the previous minor line is used instead (for example,
0.1.x alongside 0.2.x). The fixed official Git repository option follows.
Versions are ordered by Python package version semantics, not alphabetically.
Responses use `Cache-Control: no-store`.

```json
{
  "installed": false,
  "version": null,
  "source": null,
  "options": [
    {
      "id": "pypi:0.2.7",
      "label": "Qibocal 0.2.7 (PyPI)",
      "source": "pypi",
      "version": "0.2.7"
    },
    {
      "id": "git",
      "label": "Git repository (latest)",
      "source": "git",
      "version": null
    }
  ],
  "pypi_error": null,
  "git_branches": ["main", "0.1", "feature/branch"],
  "git_default_branch": "main",
  "github_error": null
}
```

Releases come from `https://pypi.org/pypi/qibocal/json`. If PyPI is unavailable
or returns invalid data, `pypi_error` explicitly describes the failure and the
Git option remains available.

Branches are fetched from the official `qiboteam/qibocal` GitHub repository,
including all pages of the branch listing. The default branch comes first,
followed by the other branches alphabetically. If GitHub is unavailable or
rate-limits the server, `github_error` describes the failure, branch choices
are empty, and the default `"git"` option remains available.

### `POST /api/admin/qibocal/install`
Uses the same strict administrator authorization as the options endpoint.

- **Body**: `{"option": "pypi:0.2.7"}`, `{"option": "git"}`, or
  `{"option": "git:feature/branch"}`.
- PyPI selections are revalidated against the server's recent compatible
  options, then installed as an exact `qibocal==<version>` pin.
- `"git"` always installs `git+https://github.com/qiboteam/qibocal.git`; arbitrary
  URLs, package names, versions outside the offered choices, and installer
  arguments are rejected.
- `"git:<branch>"` resolves the named branch through the official repository's
  GitHub API and pins installation to its verified commit SHA. Arbitrary Git
  refs and installer arguments are never interpolated into the command.
  Installed package metadata must confirm that commit before success.
- Installation upgrades/reinstalls Qibocal using the server's `sys.executable`
  through pip, or `uv pip --python <sys.executable>` when pip is unavailable.
  The installer has a ten-minute timeout.
- Installs and plot generation are synchronized. Concurrent installation
  requests return **409**.
- Success returns `{"installed": true, "version": "...", "source": "pypi"}`,
  or `"source": "git"`, only after package metadata confirms the installation.
  Responses use `Cache-Control: no-store`.

Errors return a descriptive `detail`: **400** for an invalid selection,
**401/403** for insufficient authentication/permissions, **409** for concurrent
installation or a busy generation environment, **502** for PyPI/GitHub validation or
installer failure, **503** for an unavailable installer, **504** for installation
timeout, and **500** if installed metadata cannot confirm the requested result.

Installing a version does not clear any report caches. Regenerate the current
report with its existing `/regenerate` endpoint to refresh cached outputs.

This changes the **server's Python environment**, not the browser or just the
current report. Qibocal and its resolved dependencies are shared by every report
and user on that server; other processes using the same environment can also be
affected. Run the report server in a dedicated virtual environment rather than
a shared or system-wide Python environment. Administrator authorization limits
who can request installation but does not isolate dependency changes.

### `POST /api/admin/qibocal/install/stream`
Accepts the same body and strict administrator authorization as `/install`,
but responds with `application/x-ndjson` for live installer progress. Each
newline-delimited JSON event is one of:

```json
{"type": "output", "text": "Collecting qibocal...\n"}
{"type": "complete", "status": {"installed": true, "version": "0.2.7", "source": "pypi"}}
{"type": "error", "detail": "Qibocal installation failed..."}
```

Output preserves ANSI colors. Authentication and request validation failures
use normal HTTP error responses; installation failures after streaming begins
use an `error` event. Do not treat HTTP 200 or an interrupted stream as successful
installation: wait for `complete`. Disconnecting does not interrupt the
server-side installation. The diagnostics footer uses this endpoint and
regenerates the open report or preview only after confirmed success.

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
