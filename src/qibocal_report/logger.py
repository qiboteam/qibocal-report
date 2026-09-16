"""Logging utilities for Qibocal Report Server."""

import sys
from datetime import datetime


def log_info(msg: str) -> None:
    """Log an informational message to the terminal."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = "\033[1;35m[Qibocal]\033[0m"
    time_str = f"\033[90m{timestamp}\033[0m"
    print(f"{time_str} {prefix} {msg}", flush=True)


def log_step(step: int, total: int, msg: str) -> None:
    """Log a step in a multi-step operation (e.g. protocol plotting)."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = "\033[1;35m[Qibocal]\033[0m"
    time_str = f"\033[90m{timestamp}\033[0m"
    step_str = f"\033[1;36m[{step}/{total}]\033[0m"
    print(f"{time_str} {prefix} {step_str} {msg}", flush=True)


def log_success(msg: str) -> None:
    """Log a success message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = "\033[1;32m[Qibocal ✓]\033[0m"
    time_str = f"\033[90m{timestamp}\033[0m"
    print(f"{time_str} {prefix} \033[1;32m{msg}\033[0m", flush=True)


def log_warning(msg: str) -> None:
    """Log a warning message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = "\033[1;33m[Qibocal ⚠️]\033[0m"
    time_str = f"\033[90m{timestamp}\033[0m"
    print(f"{time_str} {prefix} \033[33m{msg}\033[0m", flush=True)


def log_error(msg: str) -> None:
    """Log an error message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = "\033[1;31m[Qibocal ✗]\033[0m"
    time_str = f"\033[90m{timestamp}\033[0m"
    print(f"{time_str} {prefix} \033[31m{msg}\033[0m", file=sys.stderr, flush=True)
