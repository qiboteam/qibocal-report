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


def parse_report_directory(
    report_dir: Path,
    root_dir: Path,
    author_identities: dict[str, list[str]] | None = None,
) -> ReportSummary:
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
    raw_author = meta.get("author") or meta.get("user") or "Unknown"
    if author_identities:
        from qibocal_report.config import resolve_author_identity

        author = resolve_author_identity(raw_author, author_identities)
    else:
        author = raw_author
    platform = meta.get("platform") or "Generic QPU"
    targets = meta.get("targets") or meta.get("qubits") or []
    if not isinstance(targets, list):
        targets = [targets] if targets is not None else []
    raw_tags = (
        meta.get("tag")
        or meta.get("tags")
        or meta.get("labels")
        or meta.get("label")
        or []
    )
    if isinstance(raw_tags, str):
        tags = [raw_tags]
    elif isinstance(raw_tags, list):
        tags = [str(t) for t in raw_tags if t is not None]
    else:
        tags = []
    exec_time = meta.get("total_execution_time") or meta.get("duration") or "34.2s"
    cached = has_cached_report(report_dir)
    protocols = _discover_protocols(report_dir, meta)

    # Pre-compile search index from platform, author, tags, protocols, targets, date, id
    tag_tokens = " ".join(tags)
    proto_tokens = " ".join(protocols)
    target_tokens = " ".join(f"q{t} {t}" for t in targets)
    search_tokens = (
        f"{platform} {author} {raw_author} {tag_tokens} "
        f"{proto_tokens} {target_tokens} {date_str} {time_str} {report_id} {title}"
    )
    search_index = search_tokens.lower()

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
        tags=tags,
        labels=tags,
        total_execution_time=exec_time,
        has_cached_report=cached,
        search_index=search_index,
    )


# In-memory index cache to avoid re-scanning unchanged directories
_REPORT_CACHE: dict[str, Any] = {
    "root_path": None,
    "author_identities_key": None,
    "last_mtime": 0.0,
    "reports": None,
}


def invalidate_report_cache() -> None:
    """Invalidate the in-memory indexed reports cache."""
    _REPORT_CACHE["last_mtime"] = 0.0
    _REPORT_CACHE["reports"] = None


def get_directory_mtime(root_dir: Path) -> float:
    """Compute the maximum mtime across root_dir and its report directories."""
    if not root_dir.exists() or not root_dir.is_dir():
        return 0.0

    try:
        latest = root_dir.stat().st_mtime
    except OSError:
        return 0.0

    try:
        for dirpath, dirnames, _ in os.walk(root_dir):
            dirnames[:] = [
                d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")
            ]
            dp = Path(dirpath)
            try:
                s = dp.stat()
                latest = max(latest, s.st_mtime)
            except OSError:
                pass

            if dp != root_dir and is_report_directory(dp):
                for meta_name in ("meta.json", "history.json"):
                    meta_p = dp / meta_name
                    if meta_p.is_file():
                        try:
                            m_mtime = meta_p.stat().st_mtime
                            latest = max(latest, m_mtime)
                        except OSError:
                            pass
                report_meta = dp / "report" / "meta.json"
                if report_meta.is_file():
                    try:
                        rm_mtime = report_meta.stat().st_mtime
                        latest = max(latest, rm_mtime)
                    except OSError:
                        pass
                dirnames.clear()
    except OSError:
        pass

    return latest


def scan_reports(
    root_dir: Path,
    author_identities: dict[str, list[str]] | None = None,
) -> list[ReportSummary]:
    """Scan root_dir for reports, caching indexing and invalidating on change."""
    resolved_root = root_dir.resolve()
    if not resolved_root.exists() or not resolved_root.is_dir():
        return []

    if author_identities is None:
        try:
            from qibocal_report.config import load_servers

            for s in load_servers():
                if s.get("is_default") and s.get("author_identities"):
                    author_identities = s["author_identities"]
                    break
        except (OSError, KeyError, TypeError, ValueError):
            author_identities = None

    auth_key = (
        json.dumps(author_identities, sort_keys=True) if author_identities else ""
    )
    current_mtime = get_directory_mtime(resolved_root)

    # Check if cache is still valid
    if (
        _REPORT_CACHE["root_path"] == str(resolved_root)
        and _REPORT_CACHE["author_identities_key"] == auth_key
        and _REPORT_CACHE["reports"] is not None
        and current_mtime <= _REPORT_CACHE["last_mtime"]
    ):
        return _REPORT_CACHE["reports"]

    reports: list[ReportSummary] = []

    # Check root_dir itself
    if is_report_directory(resolved_root):
        reports = [
            parse_report_directory(
                resolved_root, resolved_root.parent, author_identities=author_identities
            )
        ]
    else:
        # Fast directory walk skipping ignored subtrees
        for dirpath, dirnames, _ in os.walk(resolved_root):
            dirnames[:] = [
                d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")
            ]
            p = Path(dirpath)

            if p != resolved_root and is_report_directory(p):
                reports.append(
                    parse_report_directory(
                        p, resolved_root, author_identities=author_identities
                    )
                )
                # Don't recurse into subdirectories of a discovered report
                dirnames.clear()

    # Update cache
    _REPORT_CACHE["root_path"] = str(resolved_root)
    _REPORT_CACHE["author_identities_key"] = auth_key
    _REPORT_CACHE["last_mtime"] = current_mtime
    _REPORT_CACHE["reports"] = reports

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
            if (r.search_index and q_lower in r.search_index)
            or q_lower in (r.title or "").lower()
            or q_lower in r.id.lower()
            or q_lower in (r.author or "").lower()
            or q_lower in (r.platform or "").lower()
            or any(q_lower in tag.lower() for tag in (r.tags or r.labels))
            or any(q_lower in p.lower() for p in r.protocols)
        ]

    if authors:
        filtered = [r for r in filtered if r.author in authors]

    if labels:
        filtered = [
            r for r in filtered if any(lab in (r.tags or r.labels) for lab in labels)
        ]

    if protocols:
        filtered = [r for r in filtered if any(p in r.protocols for p in protocols)]

    if start_date:
        filtered = [r for r in filtered if r.date >= start_date]

    if end_date:
        filtered = [r for r in filtered if r.date <= end_date]

    # Sorting
    if sort_by == "date_asc":
        filtered.sort(key=lambda r: (r.date, r.time or ""))
    elif sort_by == "platform":
        filtered.sort(key=lambda r: (r.platform or "").lower())
    elif sort_by in ("id", "title"):
        filtered.sort(key=lambda r: r.id.lower())
    else:  # date_desc default
        filtered.sort(key=lambda r: (r.date, r.time or ""), reverse=True)

    return filtered


def compute_filter_stats(reports: list[ReportSummary]) -> FilterStats:
    """Compute aggregate filter statistics (Issue #3)."""
    authors = sorted({r.author for r in reports if r.author})
    labels = sorted({lab for r in reports for lab in (r.tags or r.labels)})

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
        tags=labels,
        labels=labels,
        protocols=proto_freqs,
        date_histogram=date_histogram,
    )


def get_report_detail(
    root_dir: Path,
    report_id: str,
    author_identities: dict[str, list[str]] | None = None,
) -> ReportDetail | None:
    """Retrieve full details for a specific report."""
    target_dir = root_dir / report_id
    if not target_dir.is_dir():
        # Search by name match
        for r in scan_reports(root_dir, author_identities=author_identities):
            if r.id == report_id:
                target_dir = Path(r.path)
                break

    if not target_dir.is_dir() or not is_report_directory(target_dir):
        return None

    if author_identities is None:
        try:
            from qibocal_report.config import load_servers

            for s in load_servers():
                if s.get("is_default") and s.get("author_identities"):
                    author_identities = s["author_identities"]
                    break
        except (OSError, KeyError, TypeError, ValueError):
            author_identities = None

    summary = parse_report_directory(
        target_dir, root_dir, author_identities=author_identities
    )

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
        **summary.model_dump(),
        history=history_data,
        platform_snapshot=platform_data,
        protocols_summary=proto_summaries,
    )
