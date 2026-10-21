"""Report mutation operations (tagging, labeling, author updates, deletion)."""

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from qibocal_report.logger import log_error, log_info
from qibocal_report.models import BulkActionRequest, BulkActionResponse
from qibocal_report.reports.scanner import invalidate_report_cache, scan_reports


def find_report_dirs(root_dir: Path, report_ids: list[str]) -> list[Path]:
    """Match given report IDs against directories on disk safely."""
    import urllib.parse

    resolved_root = root_dir.resolve()
    id_set: set[str] = set()
    for rid in report_ids:
        id_set.add(rid)
        unquoted = urllib.parse.unquote(rid)
        if unquoted != rid:
            id_set.add(unquoted)

    matched: dict[str, Path] = {}

    for rid in id_set:
        candidate = (root_dir / rid).resolve()
        try:
            if (
                candidate.is_relative_to(resolved_root)
                and candidate != resolved_root
                and candidate.is_dir()
            ):
                matched[rid] = candidate
        except (ValueError, OSError):
            pass

    remaining = id_set - set(matched.keys())
    if remaining:
        for r in scan_reports(root_dir):
            if r.id in remaining or Path(r.path).name in remaining:
                cand = Path(r.path).resolve()
                try:
                    if (
                        cand.is_relative_to(resolved_root)
                        and cand != resolved_root
                        and cand.is_dir()
                    ):
                        matched[r.id] = cand
                except (ValueError, OSError):
                    pass

    return list(matched.values())


def _modify_meta_files(
    rep_dir: Path, modifier_fn: Callable[[dict[str, Any]], bool]
) -> bool:
    """Apply a mutation function to meta.json in both root and report/ subfolder."""
    meta_paths = [rep_dir / "meta.json"]
    if (rep_dir / "report" / "meta.json").is_file():
        meta_paths.append(rep_dir / "report" / "meta.json")

    updated_any = False
    for meta_path in meta_paths:
        meta_data: dict[str, Any] = {}
        if meta_path.is_file():
            try:
                meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                meta_data = {}

        if modifier_fn(meta_data):
            try:
                meta_path.write_text(json.dumps(meta_data, indent=2), encoding="utf-8")
                updated_any = True
            except OSError as err:
                log_error(f"Failed to update meta.json at {meta_path}: {err}")

    return updated_any


def protocol_targets(report_dir: Path) -> list[Any]:
    """The union of the targets the report's protocols were run on, in order.

    Each protocol's `action.yml` names its targets — qubits, or pairs as
    lists — which is better information than the session's `meta.json`,
    whose `targets` is often absent or stale. Pairs stay pairs.
    """
    import yaml

    from qibocal_report.reports.generator import get_execution_order

    found: list[Any] = []
    data = report_dir / "data"
    if not data.is_dir():
        return found
    # The protocols as they were run, then whatever the history does not name.
    folders = [data / name for name in get_execution_order(report_dir)]
    folders += sorted(f for f in data.iterdir() if f.is_dir() and f not in folders)
    for action in (f / "action.yml" for f in folders):
        if not action.is_file():
            action = action.with_suffix(".yaml")
            if not action.is_file():
                continue
        try:
            content = yaml.safe_load(action.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        targets = content.get("targets") if isinstance(content, dict) else None
        for target in targets or []:
            if target not in found:
                found.append(target)
    return found


def infer_targets(root_dir: Path, reports: list[Path] | None = None) -> dict[str, int]:
    """Write `targets-inferred` into each report's meta, from its protocols.

    The session's own `targets` is left as it is; the inferred list goes
    next to it, under `targets-inferred`, which the scanner prefers. A
    report whose meta already holds the same list is left untouched. The
    numbers of reports looked at, changed, and without protocol targets
    are answered, for the interface to say what happened.
    """
    directories = reports if reports is not None else [Path(r.path) for r in scan_reports(root_dir)]
    looked, changed, empty = 0, 0, 0
    for report_dir in directories:
        looked += 1
        targets = protocol_targets(report_dir)
        if not targets:
            empty += 1
            continue

        def write(meta: dict[str, Any], targets=targets) -> bool:
            if meta.get("targets-inferred") == targets:
                return False
            meta["targets-inferred"] = targets
            return True

        if _modify_meta_files(report_dir, write):
            changed += 1
    if changed:
        invalidate_report_cache()
    return {"reports": looked, "updated": changed, "without_targets": empty}


def _delete_reports(matched_dirs: list[Path]) -> list[str]:
    deleted = []
    for rep_dir in matched_dirs:
        try:
            shutil.rmtree(rep_dir)
            deleted.append(rep_dir.name)
            log_info(f"Deleted report folder: {rep_dir}")
        except OSError as err:
            log_error(f"Failed to delete {rep_dir}: {err}")
    return deleted


def _label_reports(matched_dirs: list[Path], tag: str) -> list[str]:
    labeled = []

    def add_label(meta_data: dict[str, Any]) -> bool:
        raw_tag = meta_data.get("tag")
        if raw_tag is None:
            tags_list = [tag]
        elif isinstance(raw_tag, list):
            tags_list = [str(t) for t in raw_tag if t is not None]
            if tag not in tags_list:
                tags_list.append(tag)
        elif isinstance(raw_tag, str):
            tags_list = [raw_tag] if raw_tag == tag else [raw_tag, tag]
        else:
            tags_list = [tag]

        meta_data["tag"] = tags_list
        for field in ("tags", "labels"):
            if (
                field in meta_data
                and isinstance(meta_data[field], list)
                and tag not in meta_data[field]
            ):
                meta_data[field].append(tag)
        return True

    for rep_dir in matched_dirs:
        if _modify_meta_files(rep_dir, add_label):
            labeled.append(rep_dir.name)
            log_info(f"Added label '{tag}' to report {rep_dir}")
    return labeled


def _unlabel_reports(matched_dirs: list[Path], tag: str) -> list[str]:
    unlabeled = []

    def remove_label(meta_data: dict[str, Any]) -> bool:
        changed = False
        for key in ("tag", "tags", "labels"):
            if key in meta_data and isinstance(meta_data[key], list):
                if tag in meta_data[key]:
                    meta_data[key] = [t for t in meta_data[key] if t != tag]
                    changed = True
            elif (
                key in meta_data
                and isinstance(meta_data[key], str)
                and meta_data[key] == tag
            ):
                meta_data[key] = []
                changed = True
        return changed

    for rep_dir in matched_dirs:
        if _modify_meta_files(rep_dir, remove_label):
            unlabeled.append(rep_dir.name)
            log_info(f"Removed label '{tag}' from report {rep_dir}")
    return unlabeled


def _update_authors(matched_dirs: list[Path], author: str) -> list[str]:
    updated_authors = []

    def set_author(meta_data: dict[str, Any]) -> bool:
        meta_data["author"] = author or None
        return True

    for rep_dir in matched_dirs:
        if _modify_meta_files(rep_dir, set_author):
            updated_authors.append(rep_dir.name)
            log_info(f"Updated author to '{author}' in report {rep_dir}")
    return updated_authors


def execute_bulk_action(root_dir: Path, req: BulkActionRequest) -> BulkActionResponse:
    """Execute bulk actions (delete, label, unlabel, author) on multiple reports."""
    log_info(
        f"Bulk action requested: '{req.action}' on {len(req.report_ids)} report(s)"
    )
    matched_dirs = find_report_dirs(root_dir, req.report_ids)

    if not matched_dirs and req.report_ids:
        log_error(f"No matching report directories found for IDs: {req.report_ids}")
        raise HTTPException(
            status_code=404,
            detail="None of the specified report folders could be found on the server.",
        )

    if req.action == "delete":
        deleted = _delete_reports(matched_dirs)
        invalidate_report_cache()
        return BulkActionResponse(
            success=True,
            action="delete",
            affected=len(deleted),
            message=f"Successfully deleted {len(deleted)} report folder(s)",
        )

    if req.action == "label":
        if not req.label or not req.label.strip():
            raise HTTPException(status_code=400, detail="Label cannot be empty")
        new_tag = req.label.strip()
        # A tag that is a path segment would be one in a URL too: `..` is collapsed there.
        if new_tag in (".", "..") or "/" in new_tag:
            raise HTTPException(status_code=400, detail="A tag cannot be '.', '..' or contain '/'")
        labeled = _label_reports(matched_dirs, new_tag)
        invalidate_report_cache()
        return BulkActionResponse(
            success=True,
            action="label",
            affected=len(labeled),
            message=f"Added label '{new_tag}' to {len(labeled)} report(s)",
        )

    if req.action == "unlabel":
        if not req.label or not req.label.strip():
            raise HTTPException(status_code=400, detail="Label cannot be empty")
        target_tag = req.label.strip()
        unlabeled = _unlabel_reports(matched_dirs, target_tag)
        invalidate_report_cache()
        return BulkActionResponse(
            success=True,
            action="unlabel",
            affected=len(unlabeled),
            message=f"Removed label '{target_tag}' from {len(unlabeled)} report(s)",
        )

    if req.action == "author":
        new_author = (req.author or "").strip()
        updated = _update_authors(matched_dirs, new_author)
        invalidate_report_cache()
        return BulkActionResponse(
            success=True,
            action="author",
            affected=len(updated),
            message=f"Updated author to '{new_author}' on {len(updated)} report(s)",
        )

    raise HTTPException(status_code=400, detail=f"Unsupported action: '{req.action}'")
