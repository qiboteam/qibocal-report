import json
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
    ChangeDirectoryRequest,
    DirectoryBreadcrumb,
    DirectoryBrowseResponse,
    DirectoryEntry,
    FilterStats,
    HealthResponse,
    PaginatedReportsResponse,
    PlatformDataResponse,
    ProtocolDetail,
    ReportDetail,
    ReportSummary,
    ServerCreate,
    ServerDirectoryInfo,
    ServerModel,
    ServerUpdate,
    SingleLabelRequest,
    UpdateAuthorRequest,
)
from qibocal_report.scanner import (
    _parse_meta_json,
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

REPORT_ROOT_DIR = Path(os.environ.get("QIBOCAL_REPORT_DIR", Path.cwd())).resolve()
ORIGINAL_ROOT_DIR = Path(
    os.environ.get("QIBOCAL_ORIGINAL_REPORT_DIR", REPORT_ROOT_DIR)
).resolve()
SERVER_NAME = os.environ.get("QIBOCAL_SERVER_NAME", "local-instance")


def set_report_root(path: Path, is_original: bool = False) -> None:
    """Set the root directory to scan for reports."""
    global REPORT_ROOT_DIR, ORIGINAL_ROOT_DIR
    resolved = path.resolve()
    if is_original or "ORIGINAL_ROOT_DIR" not in globals() or ORIGINAL_ROOT_DIR is None:
        ORIGINAL_ROOT_DIR = resolved
    REPORT_ROOT_DIR = resolved
    invalidate_report_cache()


def get_report_root() -> Path:
    """Get the current root directory."""
    return REPORT_ROOT_DIR


def get_original_root() -> Path:
    """Get the original directory where the server was spawned."""
    return ORIGINAL_ROOT_DIR


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
        original_root_dir=str(ORIGINAL_ROOT_DIR),
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
    invalidate_report_cache()
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


# --- Server Directory Management Endpoints ---
def _get_relative_current() -> str:
    """Return relative path of REPORT_ROOT_DIR compared to ORIGINAL_ROOT_DIR."""
    try:
        cur = REPORT_ROOT_DIR.resolve()
        orig = ORIGINAL_ROOT_DIR.resolve()
        if cur == orig:
            return ""
        return cur.relative_to(orig).as_posix()
    except ValueError:
        return str(REPORT_ROOT_DIR)


def _count_reports_fast(path: Path) -> int:
    """Fast count of reports in a folder without affecting main report cache."""
    from qibocal_report.scanner import IGNORED_DIRS, is_report_directory

    if not path.is_dir():
        return 0
    if is_report_directory(path):
        return 1
    count = 0
    for dirpath, dirnames, _ in os.walk(path):
        dirnames[:] = [
            d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")
        ]
        dp = Path(dirpath)
        if dp != path and is_report_directory(dp):
            count += 1
            dirnames.clear()
    return count


@app.get(
    "/api/server/directory",
    response_model=ServerDirectoryInfo,
    tags=["Server Directory"],
)
def get_server_directory_info() -> ServerDirectoryInfo:
    """Get original root and currently active server directory information."""
    reports = scan_reports(REPORT_ROOT_DIR)
    return ServerDirectoryInfo(
        original_root=str(ORIGINAL_ROOT_DIR),
        current_root=str(REPORT_ROOT_DIR),
        relative_current=_get_relative_current(),
        reports_count=len(reports),
    )


@app.get(
    "/api/server/directory/browse",
    response_model=DirectoryBrowseResponse,
    tags=["Server Directory"],
)
def browse_server_directory(
    path: str = "",
    scope: str = "original",
) -> DirectoryBrowseResponse:
    """Browse subdirectories of the originally spawned server directory or current report root."""
    from qibocal_report.scanner import IGNORED_DIRS

    base_root = (
        REPORT_ROOT_DIR.resolve()
        if scope in ("root", "current")
        else ORIGINAL_ROOT_DIR.resolve()
    )
    clean_subpath = path.strip().lstrip("/")
    target = (base_root / clean_subpath).resolve()

    # Strict security check: target must be inside or equal to base_root
    if not (target == base_root or base_root in target.parents):
        raise HTTPException(
            status_code=403,
            detail=(
                "Access forbidden: cannot browse outside server folder"
            ),
        )

    if not target.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"Directory '{clean_subpath}' not found",
        )

    # Compute breadcrumbs
    root_display_name = base_root.name or "root"
    breadcrumbs = [DirectoryBreadcrumb(name=root_display_name, path="")]
    if clean_subpath:
        rel_parts = Path(clean_subpath).parts
        accum: list[str] = []
        for part in rel_parts:
            accum.append(part)
            breadcrumbs.append(DirectoryBreadcrumb(name=part, path="/".join(accum)))

    # Compute parent path
    if target == base_root:
        parent_path = None
    else:
        parent_rel = target.parent.relative_to(base_root).as_posix()
        parent_path = "" if parent_rel == "." else parent_rel

    # List subdirectories (treating report folders as leaves and omitting them)
    from qibocal_report.scanner import is_report_directory

    subdirs: list[DirectoryEntry] = []
    try:
        for item in sorted(target.iterdir(), key=lambda x: x.name.lower()):
            if (
                item.is_dir()
                and not item.name.startswith(".")
                and item.name not in IGNORED_DIRS
                and not is_report_directory(item)
            ):
                has_sub = any(
                    c.is_dir()
                    and not c.name.startswith(".")
                    and c.name not in IGNORED_DIRS
                    and not is_report_directory(c)
                    for c in item.iterdir()
                )
                is_cur = item.resolve() == REPORT_ROOT_DIR.resolve()
                item_rel = item.relative_to(base_root).as_posix()
                count = _count_reports_fast(item)
                subdirs.append(
                    DirectoryEntry(
                        name=item.name,
                        path=item_rel,
                        has_subdirs=has_sub,
                        is_current=is_cur,
                        reports_count=count,
                    )
                )
    except PermissionError:
        pass

    current_rel = "" if target == base_root else target.relative_to(base_root).as_posix()
    is_active_root = target.resolve() == REPORT_ROOT_DIR.resolve()
    reports_in_current = _count_reports_fast(target)

    return DirectoryBrowseResponse(
        original_root=str(ORIGINAL_ROOT_DIR.resolve()),
        current_root=str(REPORT_ROOT_DIR.resolve()),
        current_browse_path=current_rel,
        parent_path=parent_path,
        breadcrumbs=breadcrumbs,
        directories=subdirs,
        is_active_root=is_active_root,
        reports_count=reports_in_current,
    )


@app.post(
    "/api/server/directory",
    response_model=ServerDirectoryInfo,
    tags=["Server Directory"],
)
def change_server_directory(req: ChangeDirectoryRequest) -> ServerDirectoryInfo:
    """Change report root directory (must be subfolder of spawned directory)."""
    from qibocal_report.scanner import is_report_directory

    orig = ORIGINAL_ROOT_DIR.resolve()
    clean_subpath = req.path.strip().lstrip("/")
    target = (orig / clean_subpath).resolve()

    # Strict security check: target must be inside or equal to ORIGINAL_ROOT_DIR
    if not (target == orig or orig in target.parents):
        raise HTTPException(
            status_code=403,
            detail=(
                "Target directory must be a subfolder of the originally spawned "
                "server folder"
            ),
        )

    if not target.is_dir():
        raise HTTPException(
            status_code=400,
            detail=(
                f"Target directory '{clean_subpath}' does not exist or is not "
                "a directory"
            ),
        )

    if is_report_directory(target):
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot select a calibration report folder as the server root directory"
            ),
        )

    set_report_root(target)
    reports = scan_reports(REPORT_ROOT_DIR)

    return ServerDirectoryInfo(
        original_root=str(orig),
        current_root=str(REPORT_ROOT_DIR),
        relative_current=_get_relative_current(),
        reports_count=len(reports),
    )


# --- Reports & Search Endpoints ---
@app.get(
    "/api/reports",
    response_model=PaginatedReportsResponse | list[ReportSummary],
    tags=["Reports"],
)
def get_reports(
    response: Response,
    q: str | None = None,
    folder: str | None = None,
    author: Annotated[list[str] | None, Query()] = None,
    platform: Annotated[list[str] | None, Query()] = None,
    protocol: Annotated[list[str] | None, Query()] = None,
    label: Annotated[list[str] | None, Query()] = None,
    tag: Annotated[list[str] | None, Query()] = None,
    qubit: Annotated[list[str] | None, Query()] = None,
    target: Annotated[list[str] | None, Query()] = None,
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
    combined_qubits = list(set((qubit or []) + (target or []))) or None
    filtered = filter_reports(
        all_reports,
        query=q,
        folder=folder,
        authors=author,
        platforms=platform,
        labels=combined_tags,
        protocols=protocol,
        qubits=combined_qubits,
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
    folder: str | None = None,
    author: Annotated[list[str] | None, Query()] = None,
    platform: Annotated[list[str] | None, Query()] = None,
    protocol: Annotated[list[str] | None, Query()] = None,
    label: Annotated[list[str] | None, Query()] = None,
    tag: Annotated[list[str] | None, Query()] = None,
    qubit: Annotated[list[str] | None, Query()] = None,
    target: Annotated[list[str] | None, Query()] = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort_by: str = "date_desc",
) -> FilterStats:
    """Return filter statistics: protocol frequencies, authors, date histogram."""
    all_reports = scan_reports(REPORT_ROOT_DIR)
    combined_tags = list(set((label or []) + (tag or []))) or None
    combined_qubits = list(set((qubit or []) + (target or []))) or None
    filtered = filter_reports(
        all_reports,
        query=q,
        folder=folder,
        authors=author,
        platforms=platform,
        labels=combined_tags,
        protocols=protocol,
        qubits=combined_qubits,
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


def _read_platform_json_or_yaml(file_prefix: Path) -> Any | None:
    for ext in (".json", ".yaml", ".yml"):
        cand = file_prefix.with_suffix(ext)
        if cand.is_file():
            try:
                with open(cand, encoding="utf-8") as f:
                    if ext in (".yaml", ".yml"):
                        import yaml

                        return yaml.safe_load(f)
                    return json.load(f)
            except Exception:
                pass
    return None


@app.get(
    "/api/reports/{report_id:path}/platform-data",
    response_model=PlatformDataResponse,
    tags=["Reports"],
)
@app.get(
    "/api/reports/{report_id:path}/platform/{platform_type}",
    response_model=PlatformDataResponse,
    tags=["Reports"],
)
def get_report_platform_data(
    report_id: str,
    platform_type: str = "new",
) -> PlatformDataResponse:
    """Get parameters.json and calibration.json trees for old or new platform."""
    log_info(f"HTTP GET platform data ({platform_type}) for '{report_id}'")
    target_dir = resolve_report_dir(REPORT_ROOT_DIR, report_id)
    norm_type = (
        "old"
        if str(platform_type).lower() in ("old", "platform", "old-platform", "old_platform")
        else "new"
    )
    plat_dir = target_dir / ("platform" if norm_type == "old" else "new_platform")

    has_old = (target_dir / "platform").is_dir()
    has_new = (target_dir / "new_platform").is_dir()

    meta = _parse_meta_json(target_dir / "meta.json")
    platform_name = meta.get("platform") or "Generic QPU"

    params_data = _read_platform_json_or_yaml(plat_dir / "parameters")
    calib_data = _read_platform_json_or_yaml(plat_dir / "calibration")

    return PlatformDataResponse(
        report_id=report_id,
        platform_name=platform_name,
        platform_type=norm_type,
        has_old_platform=has_old,
        has_new_platform=has_new,
        parameters=params_data,
        calibration=calib_data,
    )


@app.get(
    "/api/reports/{report_id:path}/platform/{platform_type}/{file_name}",
    tags=["Reports"],
)
def get_report_platform_raw_file(
    report_id: str, platform_type: str, file_name: str
) -> Response:
    """Access raw parameters.json or calibration.json inline."""
    target_dir = resolve_report_dir(REPORT_ROOT_DIR, report_id)
    norm_type = (
        "old"
        if str(platform_type).lower() in ("old", "platform", "old-platform", "old_platform")
        else "new"
    )
    plat_dir = target_dir / ("platform" if norm_type == "old" else "new_platform")
    target_file = plat_dir / file_name
    if not target_file.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"{file_name} not found in {norm_type} platform for report {report_id}",
        )
    return Response(
        content=target_file.read_bytes(),
        media_type="application/json" if target_file.suffix == ".json" else "text/plain",
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
