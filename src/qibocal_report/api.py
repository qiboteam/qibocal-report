"""FastAPI Backend Server for Qibocal Report (Issue #10, Issue #5)."""

import asyncio
import os
import sysconfig
from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from qibocal_report import config
from qibocal_report.generator import (
    get_report_protocols,
    has_cached_report,
    load_cached_protocols,
    regenerate_report,
)
from qibocal_report.logger import (
    log_error,
    log_info,
    log_success,
    log_warning,
)
from qibocal_report.models import (
    FilterStats,
    HealthResponse,
    ProtocolDetail,
    ReportDetail,
    ReportSummary,
    ServerCreate,
    ServerModel,
    ServerUpdate,
)
from qibocal_report.scanner import (
    compute_filter_stats,
    filter_reports,
    get_report_detail,
    scan_reports,
)

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

# App state configuration
REPORT_ROOT_DIR = Path(os.environ.get("QIBOCAL_REPORT_DIR", Path.cwd()))
SERVER_NAME = os.environ.get("QIBOCAL_SERVER_NAME", "local-instance")


def set_report_root(path: Path) -> None:
    """Set the root directory to scan for reports."""
    global REPORT_ROOT_DIR
    REPORT_ROOT_DIR = path.resolve()


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
        url=data.url, name=data.name, description=data.description, avatar=data.avatar
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
    return {"saved": True, "count": len(servers), "path": str(config.get_config_file())}


# --- Reports & Search Endpoints ---
@app.get("/api/reports", response_model=list[ReportSummary], tags=["Reports"])
def get_reports(
    q: str | None = None,
    author: Annotated[list[str] | None, Query()] = None,
    protocol: Annotated[list[str] | None, Query()] = None,
    label: Annotated[list[str] | None, Query()] = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort_by: str = "date_desc",
) -> list[ReportSummary]:
    """List and filter Qibocal reports."""
    all_reports = scan_reports(REPORT_ROOT_DIR)
    return filter_reports(
        all_reports,
        query=q,
        authors=author,
        labels=label,
        protocols=protocol,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
    )


@app.get("/api/reports/stats", response_model=FilterStats, tags=["Reports"])
def get_filter_statistics() -> FilterStats:
    """Return filter statistics: protocol frequencies, authors, date histogram."""
    all_reports = scan_reports(REPORT_ROOT_DIR)
    return compute_filter_stats(all_reports)


@app.websocket("/ws/reports/{report_id:path}")
async def report_websocket_endpoint(websocket: WebSocket, report_id: str):
    """WebSocket endpoint for real-time report.

    Streaming and plot generation.
    The server initiates responses and streams progress so the browser stays completely
    idle.
    """
    await websocket.accept()
    log_info(f"WebSocket client connected for report: '{report_id}'")

    target_dir = REPORT_ROOT_DIR / report_id
    if not target_dir.is_dir():
        for r in scan_reports(REPORT_ROOT_DIR):
            if r.id == report_id:
                target_dir = Path(r.path)
                break

    if not target_dir.is_dir():
        log_error(f"Report '{report_id}' not found for WebSocket client")
        await websocket.send_json(
            {"type": "error", "message": f"Report '{report_id}' not found"}
        )
        await websocket.close()
        return

    try:
        # Step 1: Send metadata immediately
        detail = get_report_detail(REPORT_ROOT_DIR, report_id)
        if detail:
            await websocket.send_json(
                {"type": "metadata", "report": detail.model_dump()}
            )

        # Step 2: Stream protocols
        if has_cached_report(target_dir):
            log_info(f"Report '{report_id}' has cached artifacts. Loading from disk...")
            await websocket.send_json(
                {"type": "status", "message": "Loading pre-cached report artifacts..."}
            )
            protocols = load_cached_protocols(target_dir)
            await websocket.send_json(
                {"type": "ready", "protocols": [p.model_dump() for p in protocols]}
            )
            log_success(
                f"Dispatched {len(protocols)} pre-cached protocol(s) over "
                f"WebSocket for '{report_id}'."
            )
        else:
            log_info(f"Report '{report_id}' needs plot generation. Starting worker...")
            await websocket.send_json(
                {
                    "type": "status",
                    "message": (
                        "Initializing protocol evaluation and plot generation..."
                    ),
                }
            )

            loop = asyncio.get_running_loop()

            def sync_progress(step: int, total: int, proto_name: str):
                try:
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_json(
                            {
                                "type": "progress",
                                "step": step,
                                "total": total,
                                "protocol": proto_name,
                                "message": (
                                    f"Plotting protocol {proto_name} "
                                    f"({step}/{total})..."
                                ),
                            }
                        ),
                        loop,
                    )
                except (RuntimeError, OSError) as err:
                    log_warning(f"Could not send WebSocket progress: {err}")

            protocols = await loop.run_in_executor(
                None,
                lambda: get_report_protocols(
                    target_dir, progress_callback=sync_progress
                ),
            )

            await websocket.send_json(
                {"type": "ready", "protocols": [p.model_dump() for p in protocols]}
            )
            log_success(
                f"Dispatched {len(protocols)} generated protocol(s) over "
                f"WebSocket for '{report_id}'."
            )

        # Keep alive loop
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        log_info(f"WebSocket client disconnected for report: '{report_id}'")
    except (RuntimeError, OSError) as err:
        log_warning(f"WebSocket session ended for '{report_id}': {err}")


@app.get(
    "/api/reports/{report_id:path}/protocols",
    response_model=list[ProtocolDetail],
    tags=["Reports"],
)
def get_protocols_for_report(report_id: str) -> list[ProtocolDetail]:
    """Get all protocol outputs (HTML and Plotly figures) for a report."""
    log_info(f"HTTP GET /protocols for '{report_id}'")
    target_dir = REPORT_ROOT_DIR / report_id
    if not target_dir.is_dir():
        # Search match
        for r in scan_reports(REPORT_ROOT_DIR):
            if r.id == report_id:
                target_dir = Path(r.path)
                break
    if not target_dir.is_dir():
        log_error(f"HTTP 404: Report '{report_id}' not found")
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    return get_report_protocols(target_dir)


@app.post(
    "/api/reports/{report_id:path}/regenerate",
    response_model=list[ProtocolDetail],
    tags=["Reports"],
)
def regenerate_report_plots(report_id: str) -> list[ProtocolDetail]:
    """Regenerate protocol plots by deleting cached report and re-evaluating."""
    log_info(f"HTTP POST /regenerate for '{report_id}'")
    target_dir = REPORT_ROOT_DIR / report_id
    if not target_dir.is_dir():
        for r in scan_reports(REPORT_ROOT_DIR):
            if r.id == report_id:
                target_dir = Path(r.path)
                break
    if not target_dir.is_dir():
        log_error(f"HTTP 404: Report '{report_id}' not found")
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    return regenerate_report(target_dir)


@app.get("/api/reports/{report_id:path}", response_model=ReportDetail, tags=["Reports"])
def get_single_report(report_id: str) -> ReportDetail:
    """Get metadata, platform snapshot, history, and protocols summary for a report."""
    log_info(f"HTTP GET metadata for '{report_id}'")
    detail = get_report_detail(REPORT_ROOT_DIR, report_id)
    if not detail:
        log_error(f"HTTP 404: Report '{report_id}' not found")
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return detail


# --- Documentation Endpoints (Issue #12) ---
@app.get(
    "/api/docs-content/{doc_name}",
    response_class=PlainTextResponse,
    tags=["Documentation"],
)
def get_documentation(doc_name: str) -> str:
    """Serve plain markdown documentation content (usage, developer, api)."""
    # 1. Shipped package location (when wheel is installed)
    # 2. Development fallbacks (repo root docs/ directory)
    candidate_paths = [
        Path(sysconfig.get_path("purelib")) / f"{doc_name}.md",
        Path(sysconfig.get_path("data")) / f"{doc_name}.md",
        Path(__file__).resolve().parents[2] / "docs" / f"{doc_name}.md",
        Path.cwd() / "docs" / f"{doc_name}.md",
    ]
    for p in candidate_paths:
        if p.is_file():
            return p.read_text(encoding="utf-8")
    raise HTTPException(status_code=404, detail=f"Documentation '{doc_name}' not found")


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

    raise HTTPException(
        status_code=404,
        detail=(
            "SPA frontend not found. Please build the frontend "
            "or run in developer mode with 'qibocal report develop'."
        ),
    )
