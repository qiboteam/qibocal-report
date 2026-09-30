"""Rich logging utilities for Qibocal Report Server."""

from __future__ import annotations

import copy
import io
import logging
import re
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any, TypedDict

import uvicorn.config
from rich.console import Console
from uvicorn.logging import AccessFormatter, DefaultFormatter

console = Console()
error_console = Console(stderr=True)

REQUEST_LOG_FMT = '%(asctime)s %(levelprefix)s "%(request_line)s" %(status_code)s'
DEFAULT_LOG_FMT = "%(asctime)s %(levelprefix)s %(message)s"
TIME_FMT = "%H:%M:%S"
LOG_HISTORY_LIMIT = 2000
LOG_ENTRY_BYTES = 16384


class LogEntry(TypedDict):
    id: int
    text: str


class LogSnapshot(TypedDict):
    entries: list[LogEntry]
    cursor: int


class LogHistory:
    """Bounded, process-local ANSI log history with monotonic cursors."""

    def __init__(
        self,
        max_entries: int = LOG_HISTORY_LIMIT,
        max_entry_bytes: int = LOG_ENTRY_BYTES,
    ):
        if max_entries < 1 or max_entry_bytes < 32:
            raise ValueError("Log history limits must be positive (at least 32 bytes).")
        self._entries: deque[LogEntry] = deque(maxlen=max_entries)
        self._max_entry_bytes = max_entry_bytes
        self._cursor = 0
        self._lock = threading.Lock()

    def append(self, text: str) -> None:
        encoded = text.encode("utf-8")
        if len(encoded) > self._max_entry_bytes:
            suffix = "\x1b[0m [truncated]\n"
            text = encoded[: self._max_entry_bytes - len(suffix)].decode(
                "utf-8", errors="ignore"
            )
            text = re.sub(r"\x1b(?:\[[0-?]*[ -/]*)?$", "", text) + suffix
        with self._lock:
            self._cursor += 1
            self._entries.append({"id": self._cursor, "text": text})

    def snapshot(self, after: int = 0) -> LogSnapshot:
        with self._lock:
            if after > self._cursor:
                after = 0
            return {
                "entries": [
                    entry.copy() for entry in self._entries if entry["id"] > after
                ],
                "cursor": self._cursor,
            }


log_history = LogHistory()


class LogCaptureHandler(logging.Handler):
    """Mirror logging records, including exception text, without terminal I/O."""

    def __init__(self):
        super().__init__()
        self._default = DefaultFormatter(
            fmt=DEFAULT_LOG_FMT, datefmt=TIME_FMT, use_colors=True
        )
        self._access = AccessFormatter(
            fmt=REQUEST_LOG_FMT, datefmt=TIME_FMT, use_colors=True
        )

    def emit(self, record: logging.LogRecord) -> None:
        # Uvicorn records can also propagate to the root capture handler.
        if getattr(record, "_qibocal_report_captured", False):
            return
        formatter = (
            self._access
            if record.name == "uvicorn.access"
            and isinstance(record.args, tuple)
            and len(record.args) == 5
            else self._default
        )
        log_history.append(formatter.format(record) + "\n")
        record.__dict__["_qibocal_report_captured"] = True


def _configure_capture(cfg: dict[str, Any]) -> None:
    cfg.setdefault("handlers", {})["diagnostics"] = {"()": LogCaptureHandler}
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        handlers = (
            cfg.setdefault("loggers", {})
            .setdefault(name, {})
            .setdefault("handlers", [])
        )
        if "diagnostics" not in handlers:
            handlers.append("diagnostics")


def get_uvicorn_log_config() -> dict[str, Any]:
    """Return timestamped Uvicorn terminal and diagnostics logging configuration."""
    cfg = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
    if "formatters" in cfg:
        if "access" in cfg["formatters"]:
            cfg["formatters"]["access"]["fmt"] = REQUEST_LOG_FMT
            cfg["formatters"]["access"]["datefmt"] = TIME_FMT
        if "default" in cfg["formatters"]:
            cfg["formatters"]["default"]["fmt"] = DEFAULT_LOG_FMT
            cfg["formatters"]["default"]["datefmt"] = TIME_FMT
    _configure_capture(cfg)
    return cfg


def setup_uvicorn_logging() -> None:
    """Configure timestamped Uvicorn output and idempotent diagnostics capture."""
    # A capture-only root would suppress both basicConfig and lastResort, losing
    # the default Python terminal output.
    if not logging.getLogger().handlers:
        logging.basicConfig()
    if "formatters" in uvicorn.config.LOGGING_CONFIG:
        if "access" in uvicorn.config.LOGGING_CONFIG["formatters"]:
            uvicorn.config.LOGGING_CONFIG["formatters"]["access"]["fmt"] = (
                REQUEST_LOG_FMT
            )
            uvicorn.config.LOGGING_CONFIG["formatters"]["access"]["datefmt"] = TIME_FMT
        if "default" in uvicorn.config.LOGGING_CONFIG["formatters"]:
            uvicorn.config.LOGGING_CONFIG["formatters"]["default"]["fmt"] = (
                DEFAULT_LOG_FMT
            )
            uvicorn.config.LOGGING_CONFIG["formatters"]["default"]["datefmt"] = TIME_FMT

    _configure_capture(uvicorn.config.LOGGING_CONFIG)
    access_fmt = AccessFormatter(fmt=REQUEST_LOG_FMT, datefmt=TIME_FMT)
    default_fmt = DefaultFormatter(fmt=DEFAULT_LOG_FMT, datefmt=TIME_FMT)
    for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        captures = [h for h in logger.handlers if isinstance(h, LogCaptureHandler)]
        if not captures:
            logger.addHandler(LogCaptureHandler())
        for duplicate in captures[1:]:
            logger.removeHandler(duplicate)
        for handler in logger.handlers:
            if name and not isinstance(handler, LogCaptureHandler):
                handler.setFormatter(
                    access_fmt if name == "uvicorn.access" else default_fmt
                )


# Apply setup on module load
setup_uvicorn_logging()


def _log(
    msg: str,
    *,
    prefix: str = "[bold magenta][Qibocal][/bold magenta]",
    err: bool = False,
) -> None:
    """Format and print a timestamped log message via Rich."""
    timestamp = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
    target = error_console if err else console
    message = f"[dim]{timestamp}[/dim] {prefix} {msg}"
    target.print(message)
    rendered = io.StringIO()
    Console(
        file=rendered,
        force_terminal=True,
        color_system=target.color_system or "truecolor",
        width=target.width,
    ).print(message)
    log_history.append(rendered.getvalue())


def log_output(text: str) -> None:
    """Mirror raw installer output, preserving ANSI and avoiding Rich markup."""
    console.file.write(text)
    console.file.flush()
    log_history.append(text)


def log_info(msg: str) -> None:
    """Log an informational message to the terminal."""
    _log(msg)


def log_step(step: int, total: int, msg: str) -> None:
    """Log a step in a multi-step operation (e.g. protocol plotting)."""
    _log(
        msg,
        prefix=(
            "[bold magenta][Qibocal][/bold magenta] "
            f"[bold cyan][{step}/{total}][/bold cyan]"
        ),
    )


def log_success(msg: str) -> None:
    """Log a success message."""
    _log(
        f"[bold green]{msg}[/bold green]", prefix="[bold green][Qibocal ✓][/bold green]"
    )


def log_warning(msg: str) -> None:
    """Log a warning message."""
    _log(f"[yellow]{msg}[/yellow]", prefix="[bold yellow][Qibocal ⚠️][/bold yellow]")


def log_error(msg: str) -> None:
    """Log an error message."""
    _log(f"[red]{msg}[/red]", prefix="[bold red][Qibocal ✗][/bold red]", err=True)
