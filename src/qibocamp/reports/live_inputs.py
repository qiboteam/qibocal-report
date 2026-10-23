"""Input fingerprints for incremental report generation."""

import json
import uuid
from pathlib import Path


def write_input_cache(report_dir: Path, inputs: dict) -> None:
    """Publish successful input fingerprints atomically."""
    report_path = report_dir / "report"
    report_path.mkdir(parents=True, exist_ok=True)
    target = report_path / ".live-inputs.json"
    temporary = target.with_name(f".live-inputs-{uuid.uuid4().hex}.json")
    try:
        temporary.write_text(json.dumps(inputs), encoding="utf-8")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def protocol_inputs(report_dir: Path) -> dict[str, list]:
    """Fingerprint task files, excluding generated artifacts and metadata."""
    data_dir = report_dir / "data"
    if not data_dir.is_dir():
        return {}
    history_path = report_dir / "history.json"
    history = (
        json.loads(history_path.read_text(encoding="utf-8"))
        if history_path.is_file()
        else None
    )
    inputs = {}
    for task_dir in sorted(data_dir.iterdir()):
        if not task_dir.is_dir() or task_dir.name.startswith("."):
            continue
        if task_dir.is_symlink():
            continue
        if history is not None and task_dir.name not in history:
            continue
        files = []
        for path in sorted(task_dir.rglob("*")):
            if path.name == "notes.json" or path.name.startswith(".notes"):
                continue
            if path.is_file() and not path.is_symlink():
                stat = path.stat()
                files.append(
                    [
                        path.relative_to(task_dir).as_posix(),
                        stat.st_mtime_ns,
                        stat.st_ctime_ns,
                        stat.st_size,
                    ]
                )
        inputs[task_dir.name] = files
    return inputs


def metadata_inputs(report_dir: Path) -> list:
    """Track metadata and comment histories separately from plot inputs."""
    files = []
    paths = [report_dir / name for name in ("meta.json", "history.json", "notes.json")]
    paths.extend(sorted((report_dir / "data").glob("*/notes.json")))
    for path in paths:
        if path.is_file():
            stat = path.stat()
            files.append(
                [
                    path.relative_to(report_dir).as_posix(),
                    stat.st_mtime_ns,
                    stat.st_ctime_ns,
                    stat.st_size,
                ]
            )
    return files
