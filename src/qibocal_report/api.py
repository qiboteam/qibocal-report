"""FastAPI Backend Server for Qibocal Report."""

import os
from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Response,
    WebSocket,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from qibocal_report import config
from qibocal_report.actions import execute_bulk_action, find_report_dirs
from qibocal_report.archive import (
    resolve_meta_file,
    resolve_protocol_data_dir,
    resolve_report_dir,
    zip_directory,
)
from qibocal_report.docs import DOCS_NAVIGATION, resolve_docs_content
from qibocal_report.generator import get_report_protocols, regenerate_report
from qibocal_report.logger import log_error, log_info
from qibocal_report.models import (
    BulkActionRequest,
    BulkActionResponse,
    FilterStats,
    HealthResponse,
    PaginatedReportsResponse,
    ProtocolDetail,
    ReportDetail,
    ReportSummary,
    ServerCreate,
    ServerModel,
    ServerUpdate,
    SingleLabelRequest,
    UpdateAuthorRequest,
)
from qibocal_report.scanner import (
    compute_filter_stats,
    filter_reports,
    get_report_detail,
    invalidate_report_cache,
    scan_reports,
)
from qibocal_report.websocket import handle_report_websocket

# Backward-compatible internal aliases
_find_report_dirs = find_report_dirs
_zip_directory = zip_directory


def _resolve_report_target_dir(report_id: str) -> Path:
    return resolve_report_dir(REPORT_ROOT_DIR, report_id)


app = FastAPI(
    title="Qibocal Report Server",
    description="REST API for serving and managing Qibocal calibration reports",
    version="0.1.0",
    docs_url="/api/docs/swagger",
    redoc_url="/api/docs/redoc",
    openapi_url="/api/openapi.json",
)

# Enable CORS for development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORT_ROOT_DIR = Path(os.environ.get("QIBOCAL_REPORT_DIR", Path.cwd()))
SERVER_NAME = os.environ.get("QIBOCAL_SERVER_NAME", "local-instance")


def set_report_root(path: Path) -> None:
    """Set the root directory to scan for reports."""
    global REPORT_ROOT_DIR
    REPORT_ROOT_DIR = path.resolve()
    invalidate_report_cache()


def get_report_root() -> Path:
    """Get the root directory."""
    return REPORT_ROOT_DIR


# --- Health Endpoint ---
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """Server health status and basic info."""
    reports = scan_reports(REPORT_ROOT_DIR)
    return HealthResponse(
        status="ok",
        server_name=SERVER_NAME,
        reports_count=len(reports),
        root_dir=str(REPORT_ROOT_DIR),
    )


# --- Server Management Endpoints ---
@app.get("/api/servers", response_model=list[ServerModel], tags=["Servers"])
def list_servers() -> list[ServerModel]:
    """List all registered servers."""
    servers = config.load_servers()
    return [ServerModel(**s) for s in servers]


@app.post("/api/servers", response_model=ServerModel, tags=["Servers"])
def create_server(data: ServerCreate) -> ServerModel:
    """Register a new server URL. Name and avatar auto-generated if omitted."""
    new_server = config.add_server(
        url=data.url,
        name=data.name,
        description=data.description,
        avatar=data.avatar,
        author_identities=data.author_identities,
    )
    return ServerModel(**new_server)


@app.put("/api/servers/{server_id}", response_model=ServerModel, tags=["Servers"])
def update_server_endpoint(server_id: str, data: ServerUpdate) -> ServerModel:
    """Update a registered server's properties."""
    updated = config.update_server(server_id, data.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Server not found")
    return ServerModel(**updated)


@app.delete("/api/servers/{server_id}", tags=["Servers"])
def delete_server_endpoint(server_id: str) -> dict[str, bool]:
    """Delete a registered server."""
    success = config.delete_server(server_id)
    if not success:
        raise HTTPException(status_code=404, detail="Server not found")
    return {"deleted": True}


@app.post("/api/servers/save", tags=["Servers"])
def save_servers_endpoint() -> dict[str, Any]:
    """Explicitly persist current servers to the configuration file."""
    servers = config.load_servers()
    config.save_servers(servers)
    return {
        "saved": True,
        "count": len(servers),
        "path": str(config.get_config_file()),
    }


# --- Reports & Search Endpoints ---
@app.get(
    "/api/reports",
    response_model=PaginatedReportsResponse | list[ReportSummary],
    tags=["Reports"],
)
def get_reports(
    response: Response,
    q: str | None = None,
    author: Annotated[list[str] | None, Query()] = None,
    platform: Annotated[list[str] | None, Query()] = None,
    protocol: Annotated[list[str] | None, Query()] = None,
    label: Annotated[list[str] | None, Query()] = None,
    tag: Annotated[list[str] | None, Query()] = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort_by: str = "date_desc",
    page: int | None = Query(None, ge=1, description="Page number (1-indexed)"),
    page_size: int | None = Query(None, ge=1, le=500, description="Items per page"),
    per_page: int | None = Query(
        None, ge=1, le=500, description="Items per page (alias)"
    ),
) -> PaginatedReportsResponse | list[ReportSummary]:
    """List and filter Qibocal reports, optionally paginated."""
    all_reports = scan_reports(REPORT_ROOT_DIR)
    combined_tags = list(set((label or []) + (tag or []))) or None
    filtered = filter_reports(
        all_reports,
        query=q,
        authors=author,
        platforms=platform,
        labels=combined_tags,
        protocols=protocol,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
    )

    total = len(filtered)
    response.headers["X-Total-Count"] = str(total)

    if page is not None or page_size is not None or per_page is not None:
        page_num = page or 1
        effective_page_size = page_size or per_page or 20
        total_pages = (
            max(1, (total + effective_page_size - 1) // effective_page_size)
            if total > 0
            else 1
        )
        start_idx = (page_num - 1) * effective_page_size
        end_idx = start_idx + effective_page_size
        items = filtered[start_idx:end_idx]

        response.headers["X-Page"] = str(page_num)
        response.headers["X-Page-Size"] = str(effective_page_size)
        response.headers["X-Total-Pages"] = str(total_pages)

        return PaginatedReportsResponse(
            items=items,
            total=total,
            page=page_num,
            page_size=effective_page_size,
            total_pages=total_pages,
        )

    return filtered


@app.get("/api/reports/stats", response_model=FilterStats, tags=["Reports"])
def get_filter_statistics(
    q: str | None = None,
    author: Annotated[list[str] | None, Query()] = None,
    platform: Annotated[list[str] | None, Query()] = None,
    protocol: Annotated[list[str] | None, Query()] = None,
    label: Annotated[list[str] | None, Query()] = None,
    tag: Annotated[list[str] | None, Query()] = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort_by: str = "date_desc",
) -> FilterStats:
    """Return filter statistics: protocol frequencies, authors, date histogram."""
    all_reports = scan_reports(REPORT_ROOT_DIR)
    combined_tags = list(set((label or []) + (tag or []))) or None
    filtered = filter_reports(
        all_reports,
        query=q,
        authors=author,
        platforms=platform,
        labels=combined_tags,
        protocols=protocol,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
    )
    return compute_filter_stats(filtered)


# --- Bulk & Single Report Actions ---
@app.post(
    "/api/reports/bulk-action", response_model=BulkActionResponse, tags=["Reports"]
)
def bulk_report_action(req: BulkActionRequest) -> BulkActionResponse:
    """Execute bulk actions (delete, label, unlabel, author) across reports."""
    return execute_bulk_action(REPORT_ROOT_DIR, req)


@app.delete(
    "/api/reports/{report_id}/label/{label_name:path}",
    response_model=BulkActionResponse,
    tags=["Reports"],
)
@app.delete(
    "/api/reports/{report_id}/tag/{label_name:path}",
    response_model=BulkActionResponse,
    tags=["Reports"],
)
def remove_single_report_label(report_id: str, label_name: str) -> BulkActionResponse:
    """Remove a label or tag from a single report."""
    return execute_bulk_action(
        REPORT_ROOT_DIR,
        BulkActionRequest(action="unlabel", report_ids=[report_id], label=label_name),
    )


@app.put(
    "/api/reports/{report_id}/author",
    response_model=BulkActionResponse,
    tags=["Reports"],
)
@app.patch(
    "/api/reports/{report_id}/author",
    response_model=BulkActionResponse,
    tags=["Reports"],
)
def update_single_report_author(
    report_id: str, body: UpdateAuthorRequest
) -> BulkActionResponse:
    """Update the author of a single report."""
    return execute_bulk_action(
        REPORT_ROOT_DIR,
        BulkActionRequest(action="author", report_ids=[report_id], author=body.author),
    )


@app.post(
    "/api/reports/{report_id}/label",
    response_model=BulkActionResponse,
    tags=["Reports"],
)
@app.post(
    "/api/reports/{report_id}/tag",
    response_model=BulkActionResponse,
    tags=["Reports"],
)
def label_single_report(
    report_id: str,
    body: SingleLabelRequest | None = None,
    label: str | None = None,
) -> BulkActionResponse:
    """Add a label or tag to a single report."""
    tag_name = (body and body.label) or label or ""
    return execute_bulk_action(
        REPORT_ROOT_DIR,
        BulkActionRequest(action="label", report_ids=[report_id], label=tag_name),
    )


@app.delete(
    "/api/reports/{report_id:path}",
    response_model=BulkActionResponse,
    tags=["Reports"],
)
def delete_single_report(report_id: str) -> BulkActionResponse:
    """Delete a single report directory."""
    return execute_bulk_action(
        REPORT_ROOT_DIR, BulkActionRequest(action="delete", report_ids=[report_id])
    )


# --- Real-Time WebSocket ---
@app.websocket("/ws/reports/{report_id:path}")
async def report_websocket_endpoint(websocket: WebSocket, report_id: str):
    """WebSocket endpoint for real-time report streaming and plot generation."""
    await handle_report_websocket(websocket, report_id, REPORT_ROOT_DIR)


# --- Protocol Outputs & Regeneration ---
@app.get(
    "/api/reports/{report_id:path}/protocols",
    response_model=list[ProtocolDetail],
    tags=["Reports"],
)
def get_protocols_for_report(report_id: str) -> list[ProtocolDetail]:
    """Get all protocol outputs (HTML and Plotly figures) for a report."""
    log_info(f"HTTP GET /protocols for '{report_id}'")
    target_dir = resolve_report_dir(REPORT_ROOT_DIR, report_id)
    return get_report_protocols(target_dir)


@app.post(
    "/api/reports/{report_id:path}/regenerate",
    response_model=list[ProtocolDetail],
    tags=["Reports"],
)
def regenerate_report_plots(report_id: str) -> list[ProtocolDetail]:
    """Regenerate protocol plots by deleting cached report and re-evaluating."""
    log_info(f"HTTP POST /regenerate for '{report_id}'")
    target_dir = resolve_report_dir(REPORT_ROOT_DIR, report_id)
    return regenerate_report(target_dir)


# --- On-the-Fly Downloads ---
@app.get("/api/reports/{report_id:path}/download/full", tags=["Reports"])
@app.get("/api/reports/{report_id:path}/download", tags=["Reports"])
def download_full_report_zip(report_id: str) -> StreamingResponse:
    """Download full protocol report folder compressed on the fly as a zip archive."""
    log_info(f"HTTP GET download full folder for '{report_id}'")
    target_dir = resolve_report_dir(REPORT_ROOT_DIR, report_id)
    safe_name = target_dir.name.replace(":", "-")
    buffer = zip_directory(target_dir, prefix=target_dir.name)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.zip"'},
    )


@app.get("/api/reports/{report_id:path}/download/new-platform", tags=["Reports"])
def download_new_platform_zip(report_id: str) -> StreamingResponse:
    """Download calibrated new_platform folder on the fly as a zip archive."""
    log_info(f"HTTP GET download new platform for '{report_id}'")
    target_dir = resolve_report_dir(REPORT_ROOT_DIR, report_id)
    new_plat = target_dir / "new_platform"
    if not new_plat.is_dir():
        log_error(f"HTTP 404: new_platform directory not found in '{report_id}'")
        raise HTTPException(
            status_code=404, detail=f"new_platform not found for report {report_id}"
        )
    safe_name = target_dir.name.replace(":", "-")
    buffer = zip_directory(new_plat, prefix="new_platform")
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_name}_new_platform.zip"'
            )
        },
    )


@app.get("/api/reports/{report_id:path}/download/old-platform", tags=["Reports"])
@app.get("/api/reports/{report_id:path}/download/platform", tags=["Reports"])
def download_old_platform_zip(report_id: str) -> StreamingResponse:
    """Download initial platform folder on the fly as a zip archive."""
    log_info(f"HTTP GET download old platform for '{report_id}'")
    target_dir = resolve_report_dir(REPORT_ROOT_DIR, report_id)
    plat = target_dir / "platform"
    if not plat.is_dir():
        log_error(f"HTTP 404: platform directory not found in '{report_id}'")
        raise HTTPException(
            status_code=404, detail=f"platform not found for report {report_id}"
        )
    safe_name = target_dir.name.replace(":", "-")
    buffer = zip_directory(plat, prefix="platform")
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_name}_old_platform.zip"'
            )
        },
    )


@app.get("/api/reports/{report_id:path}/download/data/{protocol_id}", tags=["Reports"])
@app.get(
    "/api/reports/{report_id:path}/download/protocol/{protocol_id}", tags=["Reports"]
)
def download_protocol_data_zip(report_id: str, protocol_id: str) -> StreamingResponse:
    """Download data directory for a specific protocol on the fly as a zip archive."""
    log_info(f"HTTP GET download protocol data for '{report_id}' / '{protocol_id}'")
    target_dir = resolve_report_dir(REPORT_ROOT_DIR, report_id)
    data_dir = resolve_protocol_data_dir(target_dir, protocol_id)
    if not data_dir or not data_dir.is_dir():
        log_error(
            f"HTTP 404: Protocol data not found for '{protocol_id}' in '{report_id}'"
        )
        raise HTTPException(
            status_code=404,
            detail=(
                f"Data directory for protocol '{protocol_id}' not found in report"
                f" '{report_id}'"
            ),
        )

    safe_rep = target_dir.name.replace(":", "-")
    safe_proto = data_dir.name.replace(":", "-")
    buffer = zip_directory(data_dir, prefix=data_dir.name)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_rep}_{safe_proto}.zip"'
        },
    )


@app.get("/api/reports/{report_id:path}/meta.json", tags=["Reports"])
def get_report_meta_json(report_id: str) -> Response:
    """Access meta.json as plain inline JSON for browser rendering."""
    log_info(f"HTTP GET meta.json for '{report_id}'")
    target_dir = resolve_report_dir(REPORT_ROOT_DIR, report_id)
    meta_file = resolve_meta_file(target_dir)
    if not meta_file:
        log_error(f"HTTP 404: meta.json not found in '{report_id}'")
        raise HTTPException(
            status_code=404, detail=f"meta.json not found for report {report_id}"
        )
    return Response(
        content=meta_file.read_bytes(),
        media_type="application/json",
        headers={"Content-Disposition": "inline"},
    )


@app.get("/api/reports/{report_id:path}", response_model=ReportDetail, tags=["Reports"])
def get_single_report(report_id: str) -> ReportDetail:
    """Get metadata, platform snapshot, history, and protocols summary for a report."""
    detail = get_report_detail(REPORT_ROOT_DIR, report_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return detail


# --- Documentation Endpoints ---
@app.get("/api/docs-nav", tags=["Documentation"])
def get_documentation_navigation() -> list[dict]:
    """Return the structured navigation tree for documentation."""
    return DOCS_NAVIGATION


@app.get(
    "/api/docs-content/{doc_name:path}",
    response_class=PlainTextResponse,
    tags=["Documentation"],
)
def get_documentation(doc_name: str) -> str:
    """Serve plain markdown documentation content."""
    return resolve_docs_content(doc_name)


# --- Static Files and SPA Frontend Mount ---
STATIC_DIR = Path(__file__).parent / "static"

if (STATIC_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


@app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_spa(full_path: str):
    dev_frontend_url = os.environ.get("QIBOCAL_FRONTEND_URL")
    if dev_frontend_url:
        from fastapi.responses import RedirectResponse

        target = f"{dev_frontend_url}/{full_path}".rstrip("/")
        return RedirectResponse(url=target if full_path else dev_frontend_url)

    if STATIC_DIR.is_dir() and (STATIC_DIR / "index.html").is_file():
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")

    return PlainTextResponse(
        "Qibocal Report Server running (API only mode)", status_code=200
    )
