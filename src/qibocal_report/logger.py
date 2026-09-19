"""Rich logging utilities for Qibocal Report Server."""

from __future__ import annotations

import copy
import logging
from datetime import datetime, timezone
from typing import Any

import uvicorn.config
from rich.console import Console

console = Console()
error_console = Console(stderr=True)

REQUEST_LOG_FMT = '%(asctime)s %(levelprefix)s "%(request_line)s" %(status_code)s'
DEFAULT_LOG_FMT = "%(asctime)s %(levelprefix)s %(message)s"
TIME_FMT = "%H:%M:%S"


def get_uvicorn_log_config() -> dict[str, Any]:
    """Return uvicorn logging configuration with human-readable timestamp and omitted IP address."""
    cfg = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
    if "formatters" in cfg:
        if "access" in cfg["formatters"]:
            cfg["formatters"]["access"]["fmt"] = REQUEST_LOG_FMT
            cfg["formatters"]["access"]["datefmt"] = TIME_FMT
        if "default" in cfg["formatters"]:
            cfg["formatters"]["default"]["fmt"] = DEFAULT_LOG_FMT
            cfg["formatters"]["default"]["datefmt"] = TIME_FMT
    return cfg


def setup_uvicorn_logging() -> None:
    """Configure uvicorn LOGGING_CONFIG and active loggers to log request time and omit IP address."""
    if "formatters" in uvicorn.config.LOGGING_CONFIG:
        if "access" in uvicorn.config.LOGGING_CONFIG["formatters"]:
            uvicorn.config.LOGGING_CONFIG["formatters"]["access"]["fmt"] = REQUEST_LOG_FMT
            uvicorn.config.LOGGING_CONFIG["formatters"]["access"]["datefmt"] = TIME_FMT
        if "default" in uvicorn.config.LOGGING_CONFIG["formatters"]:
            uvicorn.config.LOGGING_CONFIG["formatters"]["default"]["fmt"] = DEFAULT_LOG_FMT
            uvicorn.config.LOGGING_CONFIG["formatters"]["default"]["datefmt"] = TIME_FMT

    try:
        from uvicorn.logging import AccessFormatter, DefaultFormatter

        access_fmt = AccessFormatter(
            fmt=REQUEST_LOG_FMT,
            datefmt=TIME_FMT,
        )
        for h in logging.getLogger("uvicorn.access").handlers:
            h.setFormatter(access_fmt)

        default_fmt = DefaultFormatter(
            fmt=DEFAULT_LOG_FMT,
            datefmt=TIME_FMT,
        )
        for h in logging.getLogger("uvicorn").handlers:
            h.setFormatter(default_fmt)
        for h in logging.getLogger("uvicorn.error").handlers:
            h.setFormatter(default_fmt)
    except Exception:
        pass


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
    target.print(f"[dim]{timestamp}[/dim] {prefix} {msg}")


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
