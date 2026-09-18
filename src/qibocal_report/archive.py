"""Archive compression and report directory resolution utilities."""

import io
import zipfile
from pathlib import Path

from fastapi import HTTPException

from qibocal_report.logger import log_error
from qibocal_report.scanner import scan_reports


def resolve_report_dir(root_dir: Path, report_id: str) -> Path:
    """Resolve report folder on disk by report ID or path."""
    target_dir = root_dir / report_id
    if not target_dir.is_dir():
        for r in scan_reports(root_dir):
            if r.id == report_id:
                target_dir = Path(r.path)
                break
    if not target_dir.is_dir():
        log_error(f"HTTP 404: Report '{report_id}' not found")
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return target_dir


def zip_directory(dir_path: Path, prefix: str = "") -> io.BytesIO:
    """Compress a directory into an in-memory zip file stream."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                rel = file_path.relative_to(dir_path)
                arcname = str(Path(prefix) / rel) if prefix else str(rel)
                zf.write(file_path, arcname=arcname)
    buffer.seek(0)
    return buffer


def resolve_protocol_data_dir(target_dir: Path, protocol_id: str) -> Path | None:
    """Find the data directory for a specific protocol routine within a report."""
    candidates = [
        target_dir / "data" / protocol_id,
        target_dir / "data" / protocol_id.replace("-", "_"),
        target_dir / "data" / protocol_id.replace("_", "-"),
    ]
    for c in candidates:
        if c.is_dir():
            return c

    data_parent = target_dir / "data"
    if data_parent.is_dir():
        for sub in data_parent.iterdir():
            if sub.is_dir() and (
                sub.name == protocol_id or sub.name.startswith(f"{protocol_id}-")
            ):
                return sub
    return None


def resolve_meta_file(target_dir: Path) -> Path | None:
    """Find meta.json in the report root or report/ subdirectory."""
    root_meta = target_dir / "meta.json"
    if root_meta.is_file():
        return root_meta
    sub_meta = target_dir / "report" / "meta.json"
    if sub_meta.is_file():
        return sub_meta
    return None
