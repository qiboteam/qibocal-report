"""Archive management for qibocal-report (Issue #2).

Handles consolidation of selected reports into zip archives stored in an archive
storage directory with associated metadata.json and compact index.json.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from qibocal_report.logger import log_error, log_info, log_warning
from qibocal_report.scanner import parse_report_directory


def resolve_report_dir(root_dir: Path, report_id: str) -> Path:
    """Resolve report folder on disk by report ID or path."""
    target_dir = root_dir / report_id
    if not target_dir.is_dir():
        from qibocal_report.scanner import scan_reports

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


def get_archive_storage_dir(root_dir: Path | None = None) -> Path:
    """Return the directory where archives are stored.

    Defaults to $QIBOCAL_REPORT_ARCHIVE_DIR or `<root_dir>/.archive`.
    """
    custom = os.environ.get("QIBOCAL_REPORT_ARCHIVE_DIR")
    if custom:
        path = Path(custom)
    elif root_dir:
        path = root_dir.resolve() / ".archive"
    else:
        from qibocal_report.api import get_report_root

        path = get_report_root().resolve() / ".archive"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_directory_size(path: Path) -> int:
    """Calculate total byte size of all files in a directory."""
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def list_archives(storage_dir: Path | None = None) -> list[dict[str, Any]]:
    """List all archives with their metadata, sorted newest first."""
    s_dir = storage_dir or get_archive_storage_dir()
    archives: list[dict[str, Any]] = []

    if not s_dir.is_dir():
        return archives

    for item in s_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            meta_path = item / "metadata.json"
            if meta_path.is_file():
                try:
                    data = json.loads(meta_path.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        # Ensure size_bytes is present
                        if "size_bytes" not in data or data["size_bytes"] == 0:
                            zip_file = item / data.get("zip_filename", f"{item.name}.zip")
                            if zip_file.is_file():
                                data["size_bytes"] = zip_file.stat().st_size
                        archives.append(data)
                except (json.JSONDecodeError, OSError) as err:
                    log_warning(f"Error reading archive metadata from {meta_path}: {err}")

    # Sort descending by created_at
    archives.sort(key=lambda a: a.get("created_at", ""), reverse=True)
    return archives


def get_archive_metadata(
    archive_id: str, storage_dir: Path | None = None
) -> dict[str, Any] | None:
    """Read metadata for a specific archive."""
    s_dir = storage_dir or get_archive_storage_dir()
    clean_id = archive_id.strip()
    archive_dir = s_dir / clean_id
    meta_path = archive_dir / "metadata.json"
    if not meta_path.is_file():
        return None
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def get_archive_index(
    archive_id: str, storage_dir: Path | None = None
) -> list[dict[str, Any]] | None:
    """Read the compact report index for an archive without unzipping."""
    s_dir = storage_dir or get_archive_storage_dir()
    clean_id = archive_id.strip()
    archive_dir = s_dir / clean_id
    index_path = archive_dir / "index.json"
    if not index_path.is_file():
        return None
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def get_archive_zip_path(
    archive_id: str, storage_dir: Path | None = None
) -> Path | None:
    """Return path to the zip archive file."""
    s_dir = storage_dir or get_archive_storage_dir()
    clean_id = archive_id.strip()
    archive_dir = s_dir / clean_id
    meta = get_archive_metadata(clean_id, s_dir)
    if meta and meta.get("zip_filename"):
        zip_p = archive_dir / meta["zip_filename"]
        if zip_p.is_file():
            return zip_p
    # Fallback to any .zip in folder
    for z in archive_dir.glob("*.zip"):
        return z
    return None


def create_archive(
    report_ids: list[str],
    root_dir: Path,
    name: str | None = None,
    description: str | None = None,
    filters: dict[str, Any] | None = None,
    remove_from_active: bool = True,
    storage_dir: Path | None = None,
) -> dict[str, Any]:
    """Package selected reports into an archive folder with zip, index, and metadata."""
    if not report_ids:
        raise ValueError("At least one report ID must be specified for archiving.")

    s_dir = storage_dir or get_archive_storage_dir(root_dir)
    now = datetime.now(timezone.utc)
    ts_slug = now.strftime("%Y%m%d-%H%M%S")
    rand_slug = uuid.uuid4().hex[:6]
    archive_id = f"arc-{ts_slug}-{rand_slug}"
    archive_dir = s_dir / archive_id
    archive_dir.mkdir(parents=True, exist_ok=True)

    archive_name = name.strip() if name and name.strip() else f"Archive {now.strftime('%Y-%m-%d %H:%M')}"
    zip_filename = f"{archive_id}.zip"
    zip_path = archive_dir / zip_filename

    resolved_root = root_dir.resolve()
    valid_paths: list[tuple[str, Path, int]] = []

    # Validate all requested report folders exist
    for rid in report_ids:
        clean_id = rid.strip().strip("/")
        if not clean_id:
            continue
        r_path = (resolved_root / clean_id).resolve()
        if not (r_path == resolved_root or resolved_root in r_path.parents):
            raise ValueError(f"Report path '{clean_id}' is outside the root directory.")
        if not r_path.is_dir():
            raise FileNotFoundError(f"Report directory '{clean_id}' not found.")
        r_size = _get_directory_size(r_path)
        valid_paths.append((clean_id, r_path, r_size))

    if not valid_paths:
        raise ValueError("No valid report directories found to archive.")

    # 1. Build compact report index and create zip archive
    compact_index: list[dict[str, Any]] = []

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rid, r_path, r_size in valid_paths:
            # Parse report summary for index properties
            summary = parse_report_directory(r_path, resolved_root)
            compact_index.append(
                {
                    "id": rid,
                    "title": summary.title,
                    "date": summary.date,
                    "time": summary.time,
                    "author": summary.author,
                    "platform": summary.platform,
                    "protocols": summary.protocols,
                    "qubits": summary.targets,
                    "tags": summary.tags or summary.labels or [],
                    "size_bytes": r_size,
                }
            )

            # Add all files from report directory into zip
            for item in sorted(r_path.rglob("*")):
                if item.is_file():
                    rel_to_report = item.relative_to(r_path).as_posix()
                    arcname = f"{rid}/{rel_to_report}"
                    zf.write(item, arcname)

    # 2. Write index.json
    index_path = archive_dir / "index.json"
    index_path.write_text(json.dumps(compact_index, indent=2), encoding="utf-8")

    # 3. Write metadata.json
    zip_size = zip_path.stat().st_size
    metadata = {
        "id": archive_id,
        "name": archive_name,
        "description": (description or "").strip(),
        "created_at": now.isoformat(),
        "filters": filters or {},
        "report_count": len(compact_index),
        "size_bytes": zip_size,
        "zip_filename": zip_filename,
        "report_ids": [item["id"] for item in compact_index],
    }
    meta_path = archive_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # 4. If requested, remove archived reports from active root
    if remove_from_active:
        for rid, r_path, _ in valid_paths:
            try:
                shutil.rmtree(r_path)
                log_info(f"Removed archived report '{rid}' from active directory.")
                # Prune empty parent directories up to root
                parent = r_path.parent
                while parent != resolved_root and parent != resolved_root.parent:
                    try:
                        if not any(parent.iterdir()):
                            parent.rmdir()
                            parent = parent.parent
                        else:
                            break
                    except OSError:
                        break
            except OSError as err:
                log_warning(f"Failed to remove active report '{rid}': {err}")

    log_info(
        f"Created archive '{archive_id}' ({archive_name}) with {len(compact_index)} reports."
    )
    return metadata


def restore_archive(
    archive_id: str,
    root_dir: Path,
    report_ids: list[str] | None = None,
    delete_after_restore: bool = False,
    storage_dir: Path | None = None,
) -> dict[str, Any]:
    """Restore reports from an archive back to the active report directory."""
    s_dir = storage_dir or get_archive_storage_dir(root_dir)
    clean_id = archive_id.strip()
    archive_dir = s_dir / clean_id

    if not archive_dir.is_dir():
        raise FileNotFoundError(f"Archive '{clean_id}' not found.")

    zip_path = get_archive_zip_path(clean_id, s_dir)
    if not zip_path or not zip_path.is_file():
        raise FileNotFoundError(f"Archive zip for '{clean_id}' not found.")

    resolved_root = root_dir.resolve()
    target_ids = set(report_ids) if report_ids else None
    restored_ids: set[str] = set()

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # Security check against zip slip
            dest = (resolved_root / member.filename).resolve()
            if not (dest == resolved_root or resolved_root in dest.parents):
                continue

            # Check if this member matches target report_ids
            # member.filename starts with <report_id>/...
            parts = Path(member.filename).parts
            if not parts:
                continue

            # Determine report id prefix
            current_id = parts[0]
            if len(parts) > 1 and target_ids is not None:
                # Find matching target id prefix
                matched = False
                for tid in target_ids:
                    if member.filename == tid or member.filename.startswith(f"{tid}/"):
                        matched = True
                        current_id = tid
                        break
                if not matched:
                    continue

            restored_ids.add(current_id)
            zf.extract(member, resolved_root)

    if delete_after_restore and (target_ids is None or len(restored_ids) >= len(target_ids)):
        delete_archive(clean_id, s_dir)

    return {
        "restored_count": len(restored_ids),
        "restored_ids": sorted(list(restored_ids)),
        "archive_deleted": delete_after_restore,
    }


def delete_archive(
    archive_id: str, storage_dir: Path | None = None
) -> bool:
    """Delete an archive directory and all its contents."""
    s_dir = storage_dir or get_archive_storage_dir()
    clean_id = archive_id.strip()
    archive_dir = s_dir / clean_id
    if not archive_dir.is_dir():
        return False
    shutil.rmtree(archive_dir)
    log_info(f"Deleted archive '{clean_id}'.")
    return True


def update_archive(
    archive_id: str,
    name: str | None = None,
    description: str | None = None,
    storage_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Update archive name and/or description."""
    s_dir = storage_dir or get_archive_storage_dir()
    clean_id = archive_id.strip()
    archive_dir = s_dir / clean_id
    meta_path = archive_dir / "metadata.json"
    if not meta_path.is_file():
        return None

    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        if name is not None and name.strip():
            data["name"] = name.strip()
        if description is not None:
            data["description"] = description.strip()
        meta_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
    except (json.JSONDecodeError, OSError):
        return None
