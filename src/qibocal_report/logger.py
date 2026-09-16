"""Rich logging utilities for Qibocal Report Server."""

from datetime import datetime, timezone

from rich.console import Console

console = Console()
error_console = Console(stderr=True)


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
