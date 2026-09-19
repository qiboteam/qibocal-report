"""Command Line Interface for qibocal (Issue #9, #10, #11)."""

import os
import shutil
import subprocess
from pathlib import Path

import click
import uvicorn
from rich.console import Console
from rich.panel import Panel

from qibocal_report import config
from qibocal_report.api import set_report_root
from qibocal_report.logger import get_uvicorn_log_config


@click.group(name="qibocal")
@click.version_option(version="0.1.0", prog_name="qibocal")
def main():
    """Qibocal: Quantum calibration and characterization framework."""


@main.group(name="report")
def report():
    """Manage and serve Qibocal calibration reports."""


@report.command(name="server")
@click.argument(
    "directory",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option("--host", default="localhost", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Port to listen on.")
def server(directory: str, host: str, port: int):
    """Start the FastAPI backend server."""
    dir_path = Path(directory).resolve()
    os.environ["QIBOCAL_ORIGINAL_REPORT_DIR"] = str(dir_path)
    os.environ["QIBOCAL_REPORT_DIR"] = str(dir_path)
    set_report_root(dir_path, is_original=True)

    url = f"http://{host}:{port}"
    config.add_server(
        url=url,
        name=f"local-{dir_path.name}",
        description=f"Serving reports from {dir_path}",
        avatar="quantum-ring",
    )

    console = Console()
    console.print(
        Panel.fit(
            f"[bold cyan]📁 Reports Directory :[/bold cyan] {dir_path}\n"
            f"[bold cyan]⚙️  FastAPI Server   :[/bold cyan] {url}\n"
            f"[bold cyan]📖 REST API Docs     :[/bold cyan] {url}/api/docs/swagger\n\n"
            "[dim]Press Ctrl+C to stop the server.[/dim]",
            title="[bold magenta]⚛️  Qibocal Report Server[/bold magenta]",
            border_style="magenta",
        )
    )

    uvicorn.run(
        "qibocal_report.api:app",
        host=host,
        port=port,
        log_config=get_uvicorn_log_config(),
    )


@report.command(name="dev")
@click.argument(
    "directory",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option("--host", default="localhost", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Backend port to listen on.")
@click.option(
    "--frontend-port", default=5173, type=int, help="Frontend Vite dev server port."
)
@click.option(
    "--reload/--no-reload",
    default=True,
    help="Enable auto-reload for backend server.",
)
def dev(directory: str, host: str, port: int, frontend_port: int, reload: bool = True):
    """Serve Qibocal reports in developer mode with live Vite HMR."""
    dir_path = Path(directory).resolve()
    os.environ["QIBOCAL_ORIGINAL_REPORT_DIR"] = str(dir_path)
    os.environ["QIBOCAL_REPORT_DIR"] = str(dir_path)
    set_report_root(dir_path, is_original=True)

    # Locate frontend directory
    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    if not frontend_dir.is_dir() or not (frontend_dir / "package.json").is_file():
        frontend_dir = Path.cwd() / "frontend"

    if not frontend_dir.is_dir() or not (frontend_dir / "package.json").is_file():
        raise click.ClickException(
            f"Frontend directory not found at '{frontend_dir}'. "
            "Developer mode requires the frontend source tree."
        )

    # Determine package manager command
    if shutil.which("pnpm"):
        vite_cmd = ["pnpm", "run", "dev", "--port", str(frontend_port), "--host", host]
    elif shutil.which("npm"):
        vite_cmd = [
            "npm",
            "run",
            "dev",
            "--",
            "--port",
            str(frontend_port),
            "--host",
            host,
        ]
    elif shutil.which("npx"):
        vite_cmd = ["npx", "vite", "--port", str(frontend_port), "--host", host]
    else:
        raise click.ClickException(
            "Could not find 'pnpm' or 'npm' in PATH. "
            "Developer mode requires Node.js and pnpm or npm."
        )

    backend_url = f"http://{host}:{port}"
    frontend_url = f"http://{host}:{frontend_port}"
    os.environ["QIBOCAL_FRONTEND_URL"] = frontend_url

    # Register this server in configuration
    config.add_server(
        url=backend_url,
        name=f"local-{dir_path.name}-dev",
        description=f"Serving reports (dev mode) from {dir_path}",
        avatar="quantum-ring",
    )

    console = Console()
    dev_title = "[bold magenta]⚛️  Qibocal Report (Developer Mode)[/bold magenta]"
    panel_content = (
        f"[bold cyan]📁 Reports Directory :[/bold cyan] {dir_path}\n"
        f"[bold cyan]⚡ Vite Dev Frontend :[/bold cyan] {frontend_url}\n"
        f"[bold cyan]⚙️  Backend API       :[/bold cyan] {backend_url}\n"
        f"[bold cyan]📖 REST API Docs     :[/bold cyan] "
        f"{backend_url}/api/docs/swagger\n\n"
        "[dim]Starting Vite development server with Hot Module Replacement...[/dim]\n"
        "[dim]Press Ctrl+C to stop both backend and frontend.[/dim]"
    )
    console.print(Panel.fit(panel_content, title=dev_title, border_style="magenta"))

    env = os.environ.copy()
    env["BACKEND_URL"] = backend_url

    vite_proc = subprocess.Popen(vite_cmd, cwd=frontend_dir, env=env)

    try:
        uvicorn.run(
            "qibocal_report.api:app",
            host=host,
            port=port,
            reload=reload,
            log_config=get_uvicorn_log_config(),
        )
    finally:
        if vite_proc.poll() is None:
            console.print("\n[dim]Stopping Vite development server...[/dim]")
            vite_proc.terminate()
            try:
                vite_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                vite_proc.kill()


@report.command(name="develop", hidden=True)
@click.argument(
    "directory",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option("--host", default="localhost", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Backend port to listen on.")
@click.option(
    "--frontend-port", default=5173, type=int, help="Frontend Vite dev server port."
)
@click.option(
    "--reload/--no-reload",
    default=True,
    help="Enable auto-reload for backend server.",
)
@click.pass_context
def develop_alias(
    ctx, directory: str, host: str, port: int, frontend_port: int, reload: bool
):
    """Backward-compatible alias for 'dev'."""
    ctx.forward(dev)


@report.command(name="client")
@click.option("--host", default="127.0.0.1", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Port to listen on.")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload.")
def client(host: str, port: int, reload: bool):
    """Start the client.

    To browse and manage multiple Qibocal report servers.
    """
    url = f"http://{host}:{port}"
    console = Console()
    console.print(
        Panel.fit(
            f"[bold cyan]🌐 Client URL :[/bold cyan] {url}/#/servers\n\n"
            "[dim]Press Ctrl+C to stop the client.[/dim]",
            title="[bold magenta]⚛️  Qibocal Report Client[/bold magenta]",
            border_style="magenta",
        )
    )

    uvicorn.run(
        "qibocal_report.api:app",
        host=host,
        port=port,
        reload=reload,
        log_config=get_uvicorn_log_config(),
    )


@report.command(name="dashboard", hidden=True)
@click.option("--host", default="127.0.0.1", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Port to listen on.")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload.")
@click.pass_context
def dashboard_alias(ctx, host: str, port: int, reload: bool):
    """Backward-compatible alias for 'client'."""
    ctx.forward(client)
