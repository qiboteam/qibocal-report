"""Directory scanner and search indexing for Qibocal reports (Issue #10, Issue #3)."""

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qibocal_report.generator import (
    has_cached_report,
    load_cached_protocols,
)
from qibocal_report.models import (
    DateHistogramBin,
    FilterStats,
    ProtocolFrequency,
    ProtocolSummary,
    ReportDetail,
    ReportSummary,
)

IGNORED_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    ".git",
    "dist",
    ".devenv",
    "__pycache__",
    ".pytest_cache",
    ".gemini",
    "build",
    ".cache",
}


def is_report_directory(path: Path) -> bool:
    """Check if a directory is a genuine Qibocal report folder."""
    if not path.is_dir() or path.name.startswith("."):
        return False
    # Check if any parent component is in IGNORED_DIRS
    for part in path.parts:
        if part in IGNORED_DIRS:
            return False

    # Standard Qibocal output contains meta.json
    if (path / "meta.json").is_file():
        return True

    # Pre-cached report directory containing json artifacts
    report_sub = path / "report"
    if report_sub.is_dir() and (
        (report_sub / "meta.json").is_file() or any(report_sub.glob("*.json"))
    ):
        return True

    # Raw acquisition run directory containing action.yml in subdirectories
    data_sub = path / "data"
    return data_sub.is_dir() and (
        any(data_sub.glob("*/action.yml"))
        or any(data_sub.glob("*/results.json"))
        or any(data_sub.glob("*/data.json"))
    )


def _parse_meta_json(meta_path: Path) -> dict[str, Any]:
    """Safely parse meta.json."""
    if not meta_path.is_file():
        return {}
    try:
        with open(meta_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _discover_protocols(report_dir: Path, meta_data: dict[str, Any]) -> list[str]:
    """Discover protocols in a report folder."""
    # From meta.json
    if "protocols" in meta_data and isinstance(meta_data["protocols"], list):
        return meta_data["protocols"]
    if "actions" in meta_data and isinstance(meta_data["actions"], list):
        return meta_data["actions"]
    if "stats" in meta_data and isinstance(meta_data["stats"], dict):
        protos = list(dict.fromkeys(k.rsplit("-", 1)[0] for k in meta_data["stats"]))
        if protos:
            return protos

    # From data/ directory
    data_dir = report_dir / "data"
    if data_dir.is_dir():
        protos = [
            p.name
            for p in sorted(data_dir.iterdir())
            if p.is_dir() and not p.name.startswith(".")
        ]
        if protos:
            return protos

    # From report/ directory
    report_path = report_dir / "report"
    if report_path.is_dir():
        protos = [
            p.stem
            for p in sorted(report_path.glob("*.json"))
            if p.stem not in ("meta", "history")
        ]
        if protos:
            return protos

    return ["characterization"]


def _format_date(raw_date: str | None) -> str:
    """Normalize date string to YYYY-MM-DD."""
    if not raw_date:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    clean = raw_date.strip().split("T")[0]
    return clean


def parse_report_directory(report_dir: Path, root_dir: Path) -> ReportSummary:
    """Parse a report directory into a ReportSummary."""
    meta = _parse_meta_json(report_dir / "meta.json")

    report_id = report_dir.relative_to(root_dir).as_posix()
    title = (
        meta.get("title") or report_dir.name.replace("_", " ").replace("-", " ").title()
    )
    date_str = _format_date(meta.get("date"))
    time_str = (
        meta.get("time") or meta.get("start-time") or meta.get("start_time") or ""
    )
    author = meta.get("author") or meta.get("user") or "Unknown"
    platform = meta.get("platform") or "Generic QPU"
    targets = meta.get("targets") or meta.get("qubits") or []
    if not isinstance(targets, list):
        targets = [targets] if targets is not None else []
    labels = meta.get("labels") or meta.get("tags") or []
    if not isinstance(labels, list):
        labels = [labels] if labels is not None else []
    exec_time = meta.get("total_execution_time") or meta.get("duration") or "34.2s"
    cached = has_cached_report(report_dir)
    protocols = _discover_protocols(report_dir, meta)

    return ReportSummary(
        id=report_id,
        path=str(report_dir),
        title=title,
        date=date_str,
        time=time_str,
        author=author,
        platform=platform,
        targets=targets,
        protocols=protocols,
        labels=labels,
        total_execution_time=exec_time,
        has_cached_report=cached,
    )


def scan_reports(root_dir: Path) -> list[ReportSummary]:
    """Scan the root directory for all Qibocal report directories efficiently."""
    reports: list[ReportSummary] = []
    if not root_dir.exists() or not root_dir.is_dir():
        return reports

    # Check root_dir itself
    if is_report_directory(root_dir):
        return [parse_report_directory(root_dir, root_dir.parent)]

    # Fast directory walk skipping ignored subtrees
    for dirpath, dirnames, _ in os.walk(root_dir):
        # Exclude ignored directories in-place to avoid expensive traversal
        dirnames[:] = [
            d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")
        ]
        p = Path(dirpath)
        if p != root_dir and is_report_directory(p):
            reports.append(parse_report_directory(p, root_dir))
            # Don't recurse into subdirectories of a discovered report
            dirnames.clear()

    return reports


def filter_reports(
    reports: list[ReportSummary],
    query: str | None = None,
    authors: list[str] | None = None,
    labels: list[str] | None = None,
    protocols: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort_by: str = "date_desc",
) -> list[ReportSummary]:
    """Filter and sort reports based on search criteria."""
    filtered = list(reports)

    if query:
        q_lower = query.lower().strip()
        filtered = [
            r
            for r in filtered
            if q_lower in r.title.lower()
            or q_lower in r.id.lower()
            or q_lower in (r.author or "").lower()
            or q_lower in (r.platform or "").lower()
            or any(q_lower in lab.lower() for lab in r.labels)
            or any(q_lower in p.lower() for p in r.protocols)
        ]

    if authors:
        filtered = [r for r in filtered if r.author in authors]

    if labels:
        filtered = [r for r in filtered if any(lab in r.labels for lab in labels)]

    if protocols:
        filtered = [r for r in filtered if any(p in r.protocols for p in protocols)]

    if start_date:
        filtered = [r for r in filtered if r.date >= start_date]

    if end_date:
        filtered = [r for r in filtered if r.date <= end_date]

    # Sorting
    if sort_by == "date_asc":
        filtered.sort(key=lambda r: (r.date, r.time or ""))
    elif sort_by == "title":
        filtered.sort(key=lambda r: r.title.lower())
    else:  # date_desc default
        filtered.sort(key=lambda r: (r.date, r.time or ""), reverse=True)

    return filtered


def compute_filter_stats(reports: list[ReportSummary]) -> FilterStats:
    """Compute aggregate filter statistics (Issue #3)."""
    authors = sorted({r.author for r in reports if r.author})
    labels = sorted({lab for r in reports for lab in r.labels})

    proto_counter = Counter()
    for r in reports:
        for p in r.protocols:
            proto_counter[p] += 1

    # Sorted from most frequent to least frequent (automated suggestion, Issue #3)
    proto_freqs = [
        ProtocolFrequency(name=name, count=count)
        for name, count in proto_counter.most_common()
    ]

    date_counter = Counter(r.date for r in reports if r.date)
    date_histogram = [
        DateHistogramBin(date=d, count=date_counter[d]) for d in sorted(date_counter)
    ]

    return FilterStats(
        authors=authors,
        labels=labels,
        protocols=proto_freqs,
        date_histogram=date_histogram,
    )


def get_report_detail(root_dir: Path, report_id: str) -> ReportDetail | None:
    """Retrieve full details for a specific report."""
    target_dir = root_dir / report_id
    if not target_dir.is_dir():
        # Search by name match
        for r in scan_reports(root_dir):
            if r.id == report_id:
                target_dir = Path(r.path)
                break

    if not target_dir.is_dir() or not is_report_directory(target_dir):
        return None

    summary = parse_report_directory(target_dir, root_dir)

    # Read history.json
    history_data = {}
    hist_path = target_dir / "history.json"
    if hist_path.is_file():
        try:
            with open(hist_path, encoding="utf-8") as f:
                history_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    # Read platform/ snapshot
    platform_data = {}
    plat_dir = target_dir / "platform"
    if plat_dir.is_dir():
        for f in plat_dir.glob("*.json"):
            try:
                with open(f, encoding="utf-8") as pf:
                    platform_data[f.stem] = json.load(pf)
            except (json.JSONDecodeError, OSError):
                pass
        for f in plat_dir.glob("*.yaml"):
            try:
                import yaml

                with open(f, encoding="utf-8") as yf:
                    platform_data[f.stem] = yaml.safe_load(yf)
            except (yaml.YAMLError, OSError):
                pass

    # Protocol summaries: read from cache if available, otherwise summarize from
    # metadata
    if has_cached_report(target_dir):
        protocols = load_cached_protocols(target_dir)
        proto_summaries = [
            ProtocolSummary(
                id=p.id,
                name=p.name,
                category=p.category,
                execution_time=p.execution_time,
                status=p.status,
                num_figures=len(p.figures),
            )
            for p in protocols
        ]
    else:
        proto_summaries = [
            ProtocolSummary(
                id=p_name,
                name=p_name.replace("_", " ").title(),
                category="calibration",
                execution_time="N/A",
                status="pending",
                num_figures=0,
            )
            for p_name in summary.protocols
        ]

    return ReportDetail(
        id=summary.id,
        path=summary.path,
        title=summary.title,
        date=summary.date,
        time=summary.time,
        author=summary.author,
        platform=summary.platform,
        targets=summary.targets,
        protocols=summary.protocols,
        labels=summary.labels,
        total_execution_time=summary.total_execution_time,
        has_cached_report=has_cached_report(target_dir),
        history=history_data,
        platform_snapshot=platform_data,
        protocols_summary=proto_summaries,
    )
