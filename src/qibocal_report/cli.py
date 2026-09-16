"""Command Line Interface for qibocal (Issue #9, #10, #11)."""

import os
from pathlib import Path

import click
import uvicorn

from qibocal_report import config
from qibocal_report.api import set_report_root


@click.group(name="qibocal")
@click.version_option(version="0.1.0", prog_name="qibocal")
def main():
    """Qibocal: Quantum calibration and characterization framework."""


@main.group(name="report")
def report():
    """Manage and serve Qibocal calibration reports (Issue #9, #10, #11)."""


@report.command(name="serve")
@click.argument(
    "directory",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option("--host", default="127.0.0.1", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Port to listen on.")
@click.option(
    "--reload", is_flag=True, default=False, help="Enable auto-reload for development."
)
def serve(directory: str, host: str, port: int, reload: bool):
    """
    Serve Qibocal reports from DIRECTORY.
    Spawns both backend server and frontend web application (Issue #9, #10, #11).
    """
    dir_path = Path(directory).resolve()
    set_report_root(dir_path)
    os.environ["QIBOCAL_REPORT_DIR"] = str(dir_path)

    url = f"http://{host}:{port}"
    # Register this server in configuration
    config.add_server(
        url=url,
        name=f"local-{dir_path.name}",
        description=f"Serving reports from {dir_path}",
        avatar="quantum-ring",
    )

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel.fit(
            f"[bold cyan]📁 Reports Directory :[/bold cyan] {dir_path}\n"
            f"[bold cyan]🌐 Web Application   :[/bold cyan] {url}\n"
            f"[bold cyan]📖 REST API Docs     :[/bold cyan] {url}/api/docs/swagger\n\n"
            "[dim]Press Ctrl+C to stop the server.[/dim]",
            title="[bold magenta]⚛️  Qibocal Report Server[/bold magenta]",
            border_style="magenta",
        )
    )

    uvicorn.run("qibocal_report.api:app", host=host, port=port, reload=reload)


@report.command(name="dashboard")
@click.option("--host", default="127.0.0.1", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Port to listen on.")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload.")
def dashboard(host: str, port: int, reload: bool):
    """Start the dashboard.

    To browse and manage multiple Qibocal report servers.
    """
    url = f"http://{host}:{port}"
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel.fit(
            f"[bold cyan]🌐 Dashboard URL :[/bold cyan] {url}/#/servers\n\n"
            "[dim]Press Ctrl+C to stop the server.[/dim]",
            title="[bold magenta]⚛️  Qibocal Report Dashboard[/bold magenta]",
            border_style="magenta",
        )
    )

    uvicorn.run("qibocal_report.api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
