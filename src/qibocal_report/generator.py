"""Report generation and caching logic for qibocal-report (Issue #10)."""

import json
import re
import shutil
import subprocess
import sys
import threading
import uuid
import weakref
from collections.abc import Callable
from pathlib import Path
from typing import Any

from qibocal_report.live_inputs import protocol_inputs, write_input_cache
from qibocal_report.logger import log_info, log_success, log_warning
from qibocal_report.models import ProtocolDetail
from qibocal_report.notes import attach_protocol_notes
from qibocal_report.qibocal_environment import (
    GENERATION_TIMEOUT,
    EnvironmentOperationError,
    generation_environment,
    get_qibocal_status,
)

_REPORT_LOCKS = weakref.WeakValueDictionary()
_REPORT_LOCKS_GUARD = threading.Lock()


def report_generation_lock(report_dir: Path):
    """Serialize cache reads and generation for the same report."""
    key = str(report_dir.resolve())
    with _REPORT_LOCKS_GUARD:
        lock = _REPORT_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _REPORT_LOCKS[key] = lock
        return lock


def write_protocol_cache(report_dir: Path, protocols: list[ProtocolDetail]) -> None:
    """Atomically publish a complete cache, including incremental updates."""
    report_path = report_dir / "report"
    report_path.mkdir(parents=True, exist_ok=True)
    temporary = report_path / f".protocols-{uuid.uuid4().hex}.json"
    try:
        temporary.write_text(
            json.dumps(
                [p.model_dump(exclude={"notes"}) for p in protocols],
                default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o),
            ),
            encoding="utf-8",
        )
        temporary.replace(report_path / "protocols.json")
    finally:
        temporary.unlink(missing_ok=True)


class GenerationError(str):
    def __new__(cls, message: str, error_code: str | None = None):
        instance = super().__new__(cls, message)
        instance.error_code = error_code
        return instance


def has_cached_report(report_dir: Path) -> bool:
    """Check whether a pre-cached report folder exists."""
    report_path = report_dir / "report"
    if not report_path.is_dir():
        return False
    # Check if there are json files inside
    return any(not path.name.startswith(".") for path in report_path.glob("*.json"))


def has_html_report(report_dir: Path) -> bool:
    """Check whether qibocal already generated the static report HTML (Issue #24)."""
    return (report_dir / "index.html").is_file()


def format_execution_time(seconds: float | None) -> str:
    """Format execution duration in seconds to a human-readable string."""
    if seconds is None:
        return "N/A"
    try:
        s = float(seconds)
    except (ValueError, TypeError):
        return str(seconds)
    if s < 0:
        return "N/A"
    if s < 60:
        return f"{s:.2f}s"
    minutes = int(s // 60)
    rem_seconds = int(s % 60)
    return f"{minutes}m {rem_seconds}s"


def _extract_protocol_timing_map(report_dir: Path) -> dict[str, str]:
    """Extract protocol execution times from meta.json stats."""
    timing_map: dict[str, str] = {}
    meta_path = report_dir / "meta.json"
    if not meta_path.is_file():
        meta_path = report_dir / "report" / "meta.json"
    if not meta_path.is_file():
        return timing_map

    try:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        stats = meta.get("stats", {})
        if isinstance(stats, dict):
            for proto_id, p_stat in stats.items():
                if isinstance(p_stat, dict):
                    acq = p_stat.get("acquisition", 0.0) or 0.0
                    fit = p_stat.get("fit", 0.0) or 0.0
                    total = acq + fit
                    if total > 0:
                        timing_map[proto_id] = format_execution_time(total)
                elif isinstance(p_stat, (int, float)) and p_stat > 0:
                    timing_map[proto_id] = format_execution_time(p_stat)
    except (json.JSONDecodeError, OSError, TypeError) as err:
        log_warning(f"Error reading timing from meta.json: {err}")

    return timing_map


def get_execution_order(report_dir: Path) -> list[str]:
    """Retrieve protocol execution order for a report (Issue #3).

    Authoritative source: history.json
    Effective backup: meta.json (stats keys are sorted by execution order).
    """
    # 1. Authoritative source: history.json
    for path in [report_dir / "history.json", report_dir / "report" / "history.json"]:
        if path.is_file():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    order = []
                    for item in data:
                        if isinstance(item, str) and item.strip():
                            order.append(item.strip())
                        elif isinstance(item, dict):
                            t_id = (
                                item.get("id") or item.get("task") or item.get("name")
                            )
                            if t_id:
                                order.append(str(t_id).strip())
                    if order:
                        return order
                elif isinstance(data, dict) and data:
                    return [str(k).strip() for k in data.keys()]
            except (json.JSONDecodeError, OSError, TypeError) as err:
                log_warning(f"Error reading history.json for execution order: {err}")

    # 2. Effective backup: meta.json stats keys
    for path in [report_dir / "meta.json", report_dir / "report" / "meta.json"]:
        if path.is_file():
            try:
                with open(path, encoding="utf-8") as f:
                    meta = json.load(f)
                stats = meta.get("stats")
                if isinstance(stats, dict) and stats:
                    return [str(k).strip() for k in stats.keys()]
                protos = meta.get("protocols") or meta.get("actions")
                if isinstance(protos, list) and protos:
                    return [str(p).strip() for p in protos if p]
            except (json.JSONDecodeError, OSError, TypeError) as err:
                log_warning(f"Error reading meta.json for execution order: {err}")

    return []


def _normalize_key(k: str) -> str:
    """Normalize a routine ID or protocol name for matching."""
    return k.replace("-", "_").lower().strip()


def _base_key(k: str) -> str:
    """Extract base protocol name without numeric task index."""
    norm = _normalize_key(k)
    parts = norm.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    return norm


def sort_protocols_by_execution_order(
    protocols: list[Any],
    report_dir: Path | None = None,
    order: list[str] | None = None,
) -> list[Any]:
    """Sort protocol objects or names by their execution order (Issue #3).

    Uses history.json as authoritative source, with meta.json stats as backup.
    """
    if not protocols or len(protocols) <= 1:
        return protocols

    if order is None and report_dir is not None:
        order = get_execution_order(report_dir)

    if not order:
        return protocols

    def get_id(p: Any) -> str:
        if hasattr(p, "id"):
            return str(p.id)
        if isinstance(p, dict):
            return str(p.get("id") or p.get("name") or "")
        return str(p)

    used_slots: set[int] = set()
    assigned_slots: dict[int, int] = {}

    # Pass 1: exact matches
    for idx, p in enumerate(protocols):
        pid = get_id(p)
        for slot_idx, ord_id in enumerate(order):
            if slot_idx not in used_slots and pid == ord_id:
                used_slots.add(slot_idx)
                assigned_slots[idx] = slot_idx
                break

    # Pass 2: normalized matches (handling dashes vs underscores)
    for idx, p in enumerate(protocols):
        if idx in assigned_slots:
            continue
        pid_norm = _normalize_key(get_id(p))
        for slot_idx, ord_id in enumerate(order):
            if slot_idx not in used_slots and pid_norm == _normalize_key(ord_id):
                used_slots.add(slot_idx)
                assigned_slots[idx] = slot_idx
                break

    # Pass 3: base key matches (ignoring trailing execution index)
    for idx, p in enumerate(protocols):
        if idx in assigned_slots:
            continue
        pid_base = _base_key(get_id(p))
        for slot_idx, ord_id in enumerate(order):
            if slot_idx not in used_slots and pid_base == _base_key(ord_id):
                used_slots.add(slot_idx)
                assigned_slots[idx] = slot_idx
                break

    # Pass 4: prefix / substring matches
    for idx, p in enumerate(protocols):
        if idx in assigned_slots:
            continue
        pid_base = _base_key(get_id(p))
        for slot_idx, ord_id in enumerate(order):
            ord_base = _base_key(ord_id)
            if slot_idx not in used_slots and (
                pid_base.startswith(ord_base) or ord_base.startswith(pid_base)
            ):
                used_slots.add(slot_idx)
                assigned_slots[idx] = slot_idx
                break

    def sort_key(item: tuple[int, Any]) -> tuple[int, int]:
        orig_idx, _ = item
        slot = assigned_slots.get(orig_idx, len(order))
        return (slot, orig_idx)

    sorted_pairs = sorted(enumerate(protocols), key=sort_key)
    return [p for _, p in sorted_pairs]


def load_cached_protocols(report_dir: Path) -> list[ProtocolDetail]:
    """Load pre-cached report protocol details without importing qibocal."""
    report_path = report_dir / "report"
    protocols: list[ProtocolDetail] = []

    if not report_path.is_dir():
        return protocols

    log_info(f"Loading pre-cached report artifacts for '{report_dir.name}'...")
    timing_map = _extract_protocol_timing_map(report_dir)

    # Check for protocols.json first
    single_file = report_path / "protocols.json"
    if single_file.exists():
        try:
            with open(single_file, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    protocols = [ProtocolDetail(**p) for p in data]
                    for proto in protocols:
                        if not proto.execution_time or proto.execution_time == "N/A":
                            proto.execution_time = (
                                timing_map.get(proto.id)
                                or timing_map.get(proto.id.replace("-", "_"))
                                or timing_map.get(proto.id.replace("_", "-"))
                                or "N/A"
                            )
                    protocols = sort_protocols_by_execution_order(protocols, report_dir)
                    log_success(
                        f"Loaded {len(protocols)} pre-cached protocol(s) "
                        f"for '{report_dir.name}'"
                    )
                    return attach_protocol_notes(report_dir, protocols)
        except (json.JSONDecodeError, OSError, TypeError) as err:
            log_warning(f"Error parsing protocols.json: {err}")

    # Otherwise read all *.json files except meta.json and history.json
    for json_file in report_path.glob("*.json"):
        if json_file.name.startswith(".") or json_file.name in (
            "meta.json",
            "history.json",
            "notes.json",
        ):
            continue
        try:
            with open(json_file, encoding="utf-8") as f:
                p_data = json.load(f)
                proto_obj = ProtocolDetail(**p_data)
                if not proto_obj.execution_time or proto_obj.execution_time == "N/A":
                    proto_obj.execution_time = (
                        timing_map.get(proto_obj.id)
                        or timing_map.get(proto_obj.id.replace("-", "_"))
                        or timing_map.get(proto_obj.id.replace("_", "-"))
                        or "N/A"
                    )
                protocols.append(proto_obj)
        except (json.JSONDecodeError, OSError, TypeError) as err:
            log_warning(f"Error reading {json_file.name}: {err}")

    protocols = sort_protocols_by_execution_order(protocols, report_dir)

    log_success(
        f"Loaded {len(protocols)} pre-cached protocol(s) for '{report_dir.name}'"
    )
    return attach_protocol_notes(report_dir, protocols)


# A protocol block opens with an <h4> header, a target block with an <h5> header.
_HTML_ACTION_RE = re.compile(r'<div\s+id="[^"]+"[^>]*>\s*<h4\b')
_HTML_TARGET_RE = re.compile(r'<div\s+id="([^"]+)"[^>]*>\s*<h5\b')
_HTML_TABLE_RE = re.compile(r"<table\b.*?</table>", re.DOTALL)
_HTML_PLOTLY_RE = re.compile(r'Plotly\.newPlot\s*\(\s*"[^"]*"\s*,\s*')


def _extract_balanced_value(text: str, start: int) -> str | None:
    """Return the balanced JSON-like value starting at ``text[start]``."""
    if start >= len(text) or text[start] not in "[{":
        return None
    depth = 0
    in_str = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _parse_plotly_figures(segment: str) -> list[dict]:
    """Extract plotly figure payloads embedded by ``figure.write_html``."""
    figures: list[dict] = []
    for match in _HTML_PLOTLY_RE.finditer(segment):
        start = match.end()
        data_raw = _extract_balanced_value(segment, start)
        if not data_raw:
            continue
        try:
            data = json.loads(data_raw, parse_constant=lambda _c: None)
        except ValueError:
            continue
        rest = start + len(data_raw)
        while rest < len(segment) and segment[rest].isspace():
            rest += 1
        if rest >= len(segment) or segment[rest] != ",":
            continue
        rest += 1
        while rest < len(segment) and segment[rest].isspace():
            rest += 1
        layout_raw = _extract_balanced_value(segment, rest)
        layout: dict = {}
        if layout_raw:
            try:
                layout = json.loads(layout_raw, parse_constant=lambda _c: None)
            except ValueError:
                layout = {}
        figures.append({"data": data, "layout": layout})
    return figures


def load_html_report(report_dir: Path) -> list[ProtocolDetail] | None:
    """Parse the qibocal-generated ``index.html`` instead of re-plotting (Issue #24).

    The static report is rendered by the qibocal version that produced it,
    which may know protocols the installed Qibocal does not. Whenever the
    HTML file exists it is the authoritative rendering and must be used
    without importing qibocal. Returns ``None`` when the HTML is missing or
    cannot be parsed.
    """
    html_path = report_dir / "index.html"
    if not html_path.is_file():
        return None
    try:
        html = html_path.read_text(encoding="utf-8", errors="replace")
    except OSError as err:
        log_warning(f"Could not read static report '{html_path}': {err}")
        return None

    actions = list(_HTML_ACTION_RE.finditer(html))
    if not actions:
        log_warning(f"Static report '{html_path}' has no protocol sections")
        return None

    order = get_execution_order(report_dir)
    timing_map = _extract_protocol_timing_map(report_dir)
    targets = list(_HTML_TARGET_RE.finditer(html))
    summary_pos = html.find('id="summary"')
    content_end = summary_pos if summary_pos != -1 else len(html)

    protocols: list[ProtocolDetail] = []
    for idx, action in enumerate(actions):
        action_end = actions[idx + 1].start() if idx + 1 < len(actions) else content_end
        target_starts = [
            t.start() for t in targets if action.start() <= t.start() < action_end
        ]
        target_ids = [
            t.group(1) for t in targets if action.start() <= t.start() < action_end
        ]
        if order and idx < len(order):
            task_id = order[idx]
        elif target_ids:
            base, _, last = target_ids[0].rpartition("-")
            task_id = base if base and last.isdigit() else target_ids[0]
        else:
            task_id = f"protocol-{idx + 1}"

        tables: list[str] = []
        figures: list[dict] = []
        messages: list[str] = []
        if target_starts:
            for j, t_start in enumerate(target_starts):
                t_end = (
                    target_starts[j + 1] if j + 1 < len(target_starts) else action_end
                )
                segment = html[t_start:t_end]
                seg_tables = _HTML_TABLE_RE.findall(segment)
                seg_figures = _parse_plotly_figures(segment)
                tables.extend(seg_tables)
                figures.extend(seg_figures)
                if not seg_tables and not seg_figures:
                    body = re.sub(
                        r"<h5\b.*?</h5>", "", segment, count=1, flags=re.DOTALL
                    )
                    body = re.sub(r"<script\b.*?</script>", "", body, flags=re.DOTALL)
                    body = re.sub(r"<[^>]+>", " ", body)
                    text = re.sub(r"\s+", " ", body).strip()
                    if text:
                        messages.append(text)
        else:
            action_html = html[action.start() : action_end]
            tables = _HTML_TABLE_RE.findall(action_html)
            figures = _parse_plotly_figures(action_html)

        for n, figure in enumerate(figures):
            figure["id"] = f"{task_id}-fig{n}"

        has_output = bool(tables or figures)
        exec_time = (
            timing_map.get(task_id)
            or timing_map.get(task_id.replace("-", "_"))
            or timing_map.get(task_id.replace("_", "-"))
            or timing_map.get(task_id.rsplit("-", 1)[0])
            or "N/A"
        )
        protocols.append(
            ProtocolDetail(
                id=task_id,
                name=task_id.replace("_", " ").title(),
                category="calibration",
                execution_time=exec_time,
                status="success" if has_output else "error",
                error=None
                if has_output
                else (
                    "; ".join(messages)
                    or "No figures or tables were found in the generated report HTML."
                ),
                html="\n".join(tables),
                figures=figures,
            )
        )

    return protocols


def _generate_qibocal_protocols(
    report_dir: Path,
    protocol_ids: list[str] | None = None,
) -> tuple[list[ProtocolDetail] | None, str | None]:
    """Run Qibocal in a fresh interpreter, so version changes take effect immediately."""
    result_path = report_dir.resolve() / f".qibocal-generation-{uuid.uuid4().hex}.json"
    try:
        with generation_environment():
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "qibocal_report.generation_worker",
                    str(report_dir.resolve()),
                    str(result_path),
                    *([json.dumps(protocol_ids)] if protocol_ids is not None else []),
                ],
                capture_output=True,
                text=True,
                timeout=GENERATION_TIMEOUT,
                check=False,
            )
            if result.returncode:
                output = (result.stderr or result.stdout or "No worker output.").strip()
                return (
                    None,
                    f"Qibocal generation worker failed (exit {result.returncode}): {output[-2000:]}",
                )
            with result_path.open(encoding="utf-8") as stream:
                payload = json.load(stream)
            protocols = payload["protocols"]
            error = payload.get("error")
            return (
                [ProtocolDetail(**protocol) for protocol in protocols]
                if protocols is not None
                else None,
                GenerationError(error, payload.get("error_code")) if error else None,
            )
    except subprocess.TimeoutExpired:
        return (
            None,
            f"Qibocal plot generation timed out after {GENERATION_TIMEOUT} seconds.",
        )
    except EnvironmentOperationError as error:
        return None, error.detail
    except (OSError, ValueError, TypeError, KeyError) as error:
        return None, f"Qibocal generation worker could not return plot results: {error}"
    finally:
        try:
            result_path.unlink(missing_ok=True)
        except OSError as error:
            log_warning(
                f"Could not remove Qibocal worker result '{result_path}': {error}"
            )


def _generate_qibocal_protocols_native(
    report_dir: Path,
    protocol_ids: list[str] | None = None,
) -> tuple[list[ProtocolDetail] | None, str | None]:
    """Attempt to generate report protocols using native Qibocal if available.

    Returns:
        (protocols, None) if generation succeeded.
        (None, error_message) if Qibocal is not installed or generation failed.
    """
    try:
        from qibocal.auto.output import Output  # type: ignore

        if protocol_ids is not None:
            from qibocal.auto.task import Completed  # type: ignore
        from qibocal.cli.report import generate_figures_and_report  # type: ignore
    except ImportError as error:
        if (
            isinstance(error, ModuleNotFoundError)
            and error.name == "qibocal"
            and not get_qibocal_status().installed
        ):
            return None, GenerationError(
                "Qibocal is not installed in the environment. "
                "Install Qibocal to enable on-the-fly plot generation, "
                "or use pre-cached report outputs.",
                "qibocal_not_installed",
            )
        return None, f"Error importing Qibocal or its dependencies: {error}"
    except (AttributeError, RuntimeError, OSError) as err:
        return None, f"Error importing Qibocal: {err}"

    try:
        if protocol_ids is None:
            tasks = Output.load(report_dir).history.items()
        else:
            # Load only selected tasks; an unfinished sibling must not block updates.
            tasks = ((task_id, None) for task_id in protocol_ids)
        timing_map = _extract_protocol_timing_map(report_dir)
        generated: list[ProtocolDetail] = []
        for task_id, completed in tasks:
            task_str = str(task_id)
            if protocol_ids is not None:
                try:
                    completed = Completed.load(report_dir / "data" / task_str)
                except (
                    AttributeError,
                    RuntimeError,
                    ValueError,
                    TypeError,
                    KeyError,
                    OSError,
                    ImportError,
                ) as error:
                    message = f"Could not load routine '{task_str}': {error}"
                    log_warning(message)
                    generated.append(
                        ProtocolDetail(
                            id=task_str,
                            name=task_str.replace("_", " ").title(),
                            category="calibration",
                            execution_time=timing_map.get(task_str, "N/A"),
                            status="error",
                            error=message,
                        )
                    )
                    continue
            clean_name = (
                getattr(completed.task, "operation_name", task_str)
                .replace("_", " ")
                .title()
            )
            targets = getattr(completed.task, "targets", [])
            all_figs: list[dict] = []
            html_parts: list[str] = []
            target_errors: list[str] = []

            if targets:
                for target in targets:
                    try:
                        figs, fit_rep = generate_figures_and_report(completed, target)
                        for fig in figs:
                            if hasattr(fig, "to_json"):
                                fig_dict = json.loads(fig.to_json())
                            elif hasattr(fig, "to_dict"):
                                fig_dict = fig.to_dict()
                            elif isinstance(fig, dict):
                                fig_dict = fig
                            else:
                                continue
                            if "id" not in fig_dict:
                                fig_dict["id"] = f"{task_str}-q{target}"
                            all_figs.append(fig_dict)
                        if fit_rep:
                            html_parts.append(str(fit_rep))
                    except (
                        AttributeError,
                        RuntimeError,
                        ValueError,
                        TypeError,
                        KeyError,
                        OSError,
                        ImportError,
                    ) as r_err:
                        target_errors.append(f"Target {target}: {r_err}")
                        log_warning(
                            f"Error generating target {target} for "
                            f"'{task_str}': {r_err}"
                        )
            else:
                try:
                    figs, fit_rep = generate_figures_and_report(completed, None)
                    for fig in figs:
                        if hasattr(fig, "to_json"):
                            fig_dict = json.loads(fig.to_json())
                        elif hasattr(fig, "to_dict"):
                            fig_dict = fig.to_dict()
                        elif isinstance(fig, dict):
                            fig_dict = fig
                        else:
                            continue
                        all_figs.append(fig_dict)
                    if fit_rep:
                        html_parts.append(str(fit_rep))
                except (
                    AttributeError,
                    RuntimeError,
                    ValueError,
                    TypeError,
                    KeyError,
                    OSError,
                    ImportError,
                ) as r_err:
                    target_errors.append(str(r_err))
                    log_warning(
                        f"Error generating target-less routine '{task_str}': {r_err}"
                    )

            has_output = bool(all_figs or html_parts)
            exec_time = (
                timing_map.get(task_str)
                or timing_map.get(task_str.replace("-", "_"))
                or timing_map.get(task_str.replace("_", "-"))
                or "N/A"
            )
            generated.append(
                ProtocolDetail(
                    id=task_str,
                    name=clean_name,
                    category="calibration",
                    execution_time=exec_time,
                    status="success" if has_output and not target_errors else "error",
                    error=None
                    if has_output and not target_errors
                    else (
                        f"Qibocal could not produce all outputs for routine '{task_str}'."
                        + (" " + "; ".join(target_errors) if target_errors else "")
                    ),
                    html="\n".join(html_parts),
                    figures=all_figs,
                )
            )
        return generated, None
    except (
        AttributeError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        OSError,
        ImportError,
    ) as err:
        log_warning(f"Qibocal report generation failed for '{report_dir.name}': {err}")
        return None, f"Qibocal failed to generate report: {err}"


def _publish_report_cache(
    report_dir: Path,
    protocols: list[ProtocolDetail],
    inputs: dict | None = None,
) -> None:
    """Cache protocol outputs into the report/ folder for fast reuse."""
    report_path = report_dir / "report"
    report_path.mkdir(parents=True, exist_ok=True)

    meta_summary = {
        "protocols": [p.id for p in protocols],
        "generated_by": "qibocal-report-server",
        "count": len(protocols),
    }
    with open(report_path / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta_summary, f, indent=2)

    for p in protocols:
        with open(report_path / f"{p.id}.json", "w", encoding="utf-8") as f:
            json.dump(
                p.model_dump(exclude={"notes"}),
                f,
                indent=2,
                default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o),
            )

    write_protocol_cache(report_dir, protocols)
    if inputs is not None:
        write_input_cache(
            report_dir,
            {
                p.id: inputs[p.id]
                for p in protocols
                if p.status == "success" and p.id in inputs
            },
        )


def generate_report_on_the_fly(
    report_dir: Path, progress_callback: Callable[[int, int, str], None] | None = None
) -> list[ProtocolDetail]:
    """On-the-fly generation of protocol outputs.

    If Qibocal is available and generation succeeds, populates the report/ cache
    directory. If Qibocal is not available or generation fails, returns protocol
    details containing error messages for the dashboard.
    """
    log_info(f"Generating protocol plots on-the-fly for report '{report_dir.name}'...")

    try:
        inputs = protocol_inputs(report_dir)
    except (OSError, ValueError, TypeError) as error:
        log_warning(f"Could not fingerprint report inputs: {error}")
        inputs = None
    native_protocols, error_reason = _generate_qibocal_protocols(report_dir)

    if native_protocols:
        protocols = sort_protocols_by_execution_order(native_protocols, report_dir)
        if not any(p.status == "success" for p in native_protocols):
            log_warning(
                f"Qibocal failed to generate outputs for '{report_dir.name}': "
                + "; ".join(p.error or p.id for p in protocols)
            )
            return attach_protocol_notes(report_dir, protocols)
        log_success(
            f"Generated {len(native_protocols)} protocol(s) "
            "using native Qibocal engine."
        )
        _publish_report_cache(report_dir, protocols, inputs)
        log_success(
            f"Report '{report_dir.name}' plots generated and cached "
            f"successfully ({len(protocols)} routines)."
        )
        return attach_protocol_notes(report_dir, protocols)

    # Qibocal cannot generate the plots
    discovered_protocols: list[str] = []
    exec_order = get_execution_order(report_dir)
    if exec_order:
        discovered_protocols = list(exec_order)
    else:
        data_dir = report_dir / "data"
        if data_dir.is_dir():
            for p in sorted(data_dir.iterdir()):
                if p.is_dir() and not p.name.startswith("."):
                    discovered_protocols.append(p.name)

        if not discovered_protocols:
            meta_file = report_dir / "meta.json"
            if meta_file.exists():
                try:
                    with open(meta_file, encoding="utf-8") as f:
                        m = json.load(f)
                        discovered_protocols = (
                            m.get("protocols") or m.get("actions") or []
                        )
                except (json.JSONDecodeError, OSError):
                    pass

    if not discovered_protocols:
        discovered_protocols = [report_dir.name]

    err_msg = error_reason or (
        "Qibocal did not produce protocol outputs for this report."
    )

    protocols = []
    timing_map = _extract_protocol_timing_map(report_dir)
    total = len(discovered_protocols)
    for idx, proto in enumerate(discovered_protocols):
        clean_name = proto.replace("_", " ").title()
        if progress_callback:
            try:
                progress_callback(idx + 1, total, clean_name)
            except (TypeError, RuntimeError, OSError):
                pass
        exec_time = (
            timing_map.get(proto)
            or timing_map.get(proto.replace("-", "_"))
            or timing_map.get(proto.replace("_", "-"))
            or "N/A"
        )
        protocols.append(
            ProtocolDetail(
                id=proto,
                name=clean_name,
                category="calibration",
                execution_time=exec_time,
                status="error",
                error=err_msg,
                error_code=getattr(error_reason, "error_code", None),
                html="",
                figures=[],
            )
        )

    protocols = sort_protocols_by_execution_order(protocols, report_dir)
    log_warning(f"Plots could not be generated for '{report_dir.name}': {err_msg}")
    return attach_protocol_notes(report_dir, protocols)


def get_report_protocols(
    report_dir: Path, progress_callback: Callable[[int, int, str], None] | None = None
) -> list[ProtocolDetail]:
    """Retrieve report protocols: pre-cached if present, then the
    qibocal-generated static HTML (Issue #24), otherwise on-the-fly."""
    with report_generation_lock(report_dir):
        if has_cached_report(report_dir):
            protocols = load_cached_protocols(report_dir)
        elif has_html_report(report_dir):
            protocols = load_html_report(report_dir)
            if protocols is None:
                protocols = generate_report_on_the_fly(
                    report_dir, progress_callback=progress_callback
                )
            else:
                log_success(
                    f"Rendered {len(protocols)} protocol(s) from the static "
                    f"report for '{report_dir.name}'."
                )
                try:
                    inputs = protocol_inputs(report_dir)
                except (OSError, ValueError, TypeError):
                    inputs = None
                _publish_report_cache(report_dir, protocols, inputs)
        else:
            protocols = generate_report_on_the_fly(
                report_dir, progress_callback=progress_callback
            )
        return sort_protocols_by_execution_order(protocols, report_dir)


def regenerate_report(
    report_dir: Path, progress_callback: Callable[[int, int, str], None] | None = None
) -> list[ProtocolDetail]:
    """
    Explicit request for plots regeneration (Issue #10):
    Deletes the existing report/ folder and regenerates all protocol plots.
    """
    with report_generation_lock(report_dir):
        log_info(
            f"Regenerating plots: removing existing cache for '{report_dir.name}'..."
        )
        report_path = report_dir / "report"
        if report_path.is_dir():
            shutil.rmtree(report_path)
        return generate_report_on_the_fly(
            report_dir, progress_callback=progress_callback
        )
