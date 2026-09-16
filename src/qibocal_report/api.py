"""FastAPI Backend Server for Qibocal Report (Issue #10, Issue #5)."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from qibocal_report import config
from qibocal_report.generator import get_report_protocols, regenerate_report
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
    openapi_url="/api/openapi.json"
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
        root_dir=str(REPORT_ROOT_DIR)
    )


# --- Server Management Endpoints (Issue #4, #11) ---
@app.get("/api/servers", response_model=List[ServerModel], tags=["Servers"])
def list_servers() -> List[ServerModel]:
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
        avatar=data.avatar
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
def delete_server_endpoint(server_id: str) -> Dict[str, bool]:
    """Delete a registered server."""
    success = config.delete_server(server_id)
    if not success:
        raise HTTPException(status_code=404, detail="Server not found")
    return {"deleted": True}


@app.post("/api/servers/save", tags=["Servers"])
def save_servers_endpoint() -> Dict[str, Any]:
    """Explicitly persist current servers to the configuration file."""
    servers = config.load_servers()
    config.save_servers(servers)
    return {"saved": True, "count": len(servers), "path": str(config.get_config_file())}


# --- Reports & Search Endpoints (Issue #10, #3) ---
@app.get("/api/reports", response_model=List[ReportSummary], tags=["Reports"])
def get_reports(
    q: Optional[str] = None,
    author: Optional[List[str]] = Query(None),
    protocol: Optional[List[str]] = Query(None),
    label: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "date_desc"
) -> List[ReportSummary]:
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
        sort_by=sort_by
    )


@app.get("/api/reports/stats", response_model=FilterStats, tags=["Reports"])
def get_filter_statistics() -> FilterStats:
    """Return filter statistics: protocol frequencies, authors, date histogram."""
    all_reports = scan_reports(REPORT_ROOT_DIR)
    return compute_filter_stats(all_reports)


@app.get("/api/reports/{report_id:path}/protocols", response_model=List[ProtocolDetail], tags=["Reports"])
def get_protocols_for_report(report_id: str) -> List[ProtocolDetail]:
    """Get all protocol outputs (HTML and Plotly figures) for a report."""
    target_dir = REPORT_ROOT_DIR / report_id
    if not target_dir.is_dir():
        # Search match
        for r in scan_reports(REPORT_ROOT_DIR):
            if r.id == report_id:
                target_dir = Path(r.path)
                break
    if not target_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    return get_report_protocols(target_dir)


@app.post("/api/reports/{report_id:path}/regenerate", response_model=List[ProtocolDetail], tags=["Reports"])
def regenerate_report_plots(report_id: str) -> List[ProtocolDetail]:
    """Regenerate protocol plots by deleting cached report and re-evaluating."""
    target_dir = REPORT_ROOT_DIR / report_id
    if not target_dir.is_dir():
        for r in scan_reports(REPORT_ROOT_DIR):
            if r.id == report_id:
                target_dir = Path(r.path)
                break
    if not target_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    return regenerate_report(target_dir)


@app.get("/api/reports/{report_id:path}", response_model=ReportDetail, tags=["Reports"])
def get_single_report(report_id: str) -> ReportDetail:
    """Get metadata, platform snapshot, history, and protocols summary for a report."""
    detail = get_report_detail(REPORT_ROOT_DIR, report_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return detail


# --- Documentation Endpoints (Issue #12) ---
@app.get("/api/docs-content/{doc_name}", response_class=PlainTextResponse, tags=["Documentation"])
def get_documentation(doc_name: str) -> str:
    """Serve plain markdown documentation content (usage, developer, api)."""
    # Look in package static/docs or repo docs
    candidate_paths = [
        Path(__file__).parent / "static" / "docs" / f"{doc_name}.md",
        Path(__file__).parent.parent.parent / "docs" / f"{doc_name}.md",
        Path.cwd() / "docs" / f"{doc_name}.md",
    ]
    for p in candidate_paths:
        if p.is_file():
            return p.read_text(encoding="utf-8")
    raise HTTPException(status_code=404, detail=f"Documentation '{doc_name}' not found")


# --- Static Files and SPA Frontend Mount ---
STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.is_dir() and (STATIC_DIR / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
